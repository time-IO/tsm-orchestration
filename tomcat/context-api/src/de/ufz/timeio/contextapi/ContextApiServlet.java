package de.ufz.timeio.contextapi;

import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.nio.file.attribute.PosixFilePermissions;
import java.security.MessageDigest;
import java.util.Arrays;
import java.util.regex.Pattern;

/** Writes Tomcat context descriptors of FROST instances: PUT /contexts/{schema} with user, password, url. */
public class ContextApiServlet extends HttpServlet {

    // No dots, slashes or '#' (Tomcat maps '#' in descriptor names to '/').
    private static final Pattern SCHEMA = Pattern.compile("[A-Za-z0-9_-]+");
    private static final Pattern USER_PATTERN = Pattern.compile("[A-Za-z0-9_]+");
    // No query string: pgjdbc options like socketFactory instantiate arbitrary classes.
    private static final Pattern URL_PATTERN = Pattern.compile("postgresql://[A-Za-z0-9.-]+(:[0-9]+)?/[A-Za-z0-9_-]+");

    private static final String TEMPLATE = """
            <Context docBase="/share/FROST-Server.war">
                <Parameter override="false" name="ApiVersion" value="v1.0" description="The version tag of the API used in the URL."/>
                <Parameter override="false" name="serviceRootUrl" value="%s" description="The base URL of the SensorThings Server without version."/>
                <Parameter override="false" name="defaultCount" value="false" description="The default value for the $count query option."/>
                <Parameter override="false" name="defaultTop" value="100" description="The default value for the $top query option."/>
                <Parameter override="false" name="maxTop" value="100000" description="The maximum allowed value for the $top query option."/>
                <Parameter override="false" name="maxDataSize" value="25000000" description="The maximum allowed estimated data size (in bytes) for responses."/>
                <Parameter override="false" name="bus.busImplementationClass" value="de.fraunhofer.iosb.ilt.frostserver.messagebus.InternalMessageBus" description="The java class used for connecting to the message bus."/>
                <Parameter override="false" name="persistence.persistenceManagerImplementationClass" value="de.fraunhofer.iosb.ilt.frostserver.persistence.pgjooq.imp.PostgresPersistenceManagerLong" description="The java class used for persistence (must implement PersistenceManaher interface)"/>
                <Parameter override="false" name="persistence.idGenerationMode" value="ServerGeneratedOnly" description="Mode for id generation when using PostgresPersistenceManagerString."/>
                <Parameter override="false" name="persistence.autoUpdateDatabase" value="false" description="Automatically apply database updates."/>
                <Parameter override="false" name="persistence.alwaysOrderbyId" value="false" description="Always add an 'orderby=id asc' to queries to ensure consistent paging."/>
                <Parameter override="false" name="persistence.db_jndi_datasource" value="jdbc/sensorThings" description="JNDI data source name"/>
                <Parameter override="false" name="persistence.queryTimeout" value="120" description="The maximum duration, in seconds, that a query is allowed to take."/>
                <Parameter override="false" name="plugins.openApi.enable" value="true" description="Toggle indicating whether the OpenAPI plugin should be enabled."/>
                <Resource
                    name="jdbc/sensorThings" auth="Container"
                    type="javax.sql.DataSource" driverClassName="org.postgresql.Driver"
                    url="jdbc:%s"
                    username="%s" password="%s"
                    maxTotal="20" minIdle="10" maxIdle="10" maxWaitMillis="-1"
                    testWhileIdle="true" validationQuery="SELECT 1"
                    timeBetweenEvictionRunsMillis="30000"
                    minEvictableIdleTimeMillis="60000"
                    defaultAutoCommit="false"
                />
            </Context>
            """;

    private byte[] token;
    private String serviceRootUrl;
    private Path contextDir;

    @Override
    public void init() {
        String t = env("FROST_CONTEXT_API_TOKEN");
        token = t == null ? null : t.getBytes(StandardCharsets.UTF_8);
        serviceRootUrl = env("FROST_SERVICE_ROOT_URL");
        contextDir = Path.of(System.getProperty("catalina.base"), "conf", "Catalina", "localhost")
                .toAbsolutePath().normalize();
    }

    @Override
    protected void service(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException {
        if (token == null) {
            reply(resp, 503, "{\"error\":\"FROST_CONTEXT_API_TOKEN is not configured\"}");
        } else if (serviceRootUrl == null) {
            reply(resp, 503, "{\"error\":\"FROST_SERVICE_ROOT_URL is not configured\"}");
        } else if (!authorized(req)) {
            resp.setHeader("WWW-Authenticate", "Bearer");
            reply(resp, 401, "{\"error\":\"unauthorized\"}");
        } else {
            super.service(req, resp);
        }
    }

    @Override
    protected void doPut(HttpServletRequest req, HttpServletResponse resp) throws IOException {
        String schema = schemaOf(req);
        String user = req.getParameter("user");
        String password = req.getParameter("password");
        String url = req.getParameter("url");
        if (schema == null) {
            reply(resp, 400, "{\"error\":\"invalid schema name\"}");
            return;
        }
        if (user == null || !USER_PATTERN.matcher(user).matches()
                || url == null || !URL_PATTERN.matcher(url).matches()
                || !validPassword(password)) {
            reply(resp, 400, "{\"schema\":\"" + schema + "\",\"error\":\"user, password and url are required and must be valid\"}");
            return;
        }
        String xml = TEMPLATE.formatted(escape(serviceRootUrl + schema), url, user, escape(password));
        boolean changed;
        try {
            changed = write(contextDir.resolve(schema + ".xml"), xml.getBytes(StandardCharsets.UTF_8));
        } catch (IOException | RuntimeException e) {
            log("writing context " + schema + " failed", e);
            reply(resp, 500, "{\"schema\":\"" + schema + "\",\"error\":\"writing context failed\"}");
            return;
        }
        reply(resp, 200, "{\"schema\":\"" + schema + "\",\"changed\":" + changed + "}");
    }

    // XML 1.0 can't represent other control chars, even escaped; Tomcat would fail to parse the descriptor.
    private static boolean validPassword(String password) {
        return password != null && !password.isEmpty() && password.chars()
                .noneMatch(c -> c < 0x20 && c != '\t' && c != '\n' && c != '\r' || c == 0xFFFE || c == 0xFFFF);
    }

    /** Returns null for unset or empty variables. */
    private static String env(String name) {
        String v = System.getenv(name);
        return v == null || v.isEmpty() ? null : v;
    }

    private boolean authorized(HttpServletRequest req) {
        String header = req.getHeader("Authorization");
        if (header == null || !header.startsWith("Bearer ")) {
            return false;
        }
        byte[] given = header.substring(7).getBytes(StandardCharsets.UTF_8);
        return MessageDigest.isEqual(given, token);
    }

    private static String schemaOf(HttpServletRequest req) {
        String info = req.getPathInfo();
        if (info == null || info.length() < 2) {
            return null;
        }
        String schema = info.substring(1);
        // ROOT.xml would replace the root webapp.
        return SCHEMA.matcher(schema).matches() && !schema.equals("ROOT") ? schema : null;
    }

    /** Returns false if the content is unchanged. */
    private static boolean write(Path target, byte[] content) throws IOException {
        // Rewriting identical content would make Tomcat redeploy the context.
        if (Files.exists(target) && Arrays.equals(Files.readAllBytes(target), content)) {
            return false;
        }
        // Non-.xml temp name + rename, so Tomcat never deploys a half-written descriptor.
        Path tmp = Files.createTempFile(target.getParent(), ".", ".tmp",
                PosixFilePermissions.asFileAttribute(PosixFilePermissions.fromString("rw-------")));
        try {
            Files.write(tmp, content);
            Files.move(tmp, target, StandardCopyOption.ATOMIC_MOVE, StandardCopyOption.REPLACE_EXISTING);
        } finally {
            Files.deleteIfExists(tmp);
        }
        return true;
    }

    private static String escape(String s) {
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                .replace("\"", "&quot;").replace("'", "&apos;")
                // Attribute-value normalization would turn these into spaces.
                .replace("\n", "&#10;").replace("\r", "&#13;").replace("\t", "&#9;");
    }

    private static void reply(HttpServletResponse resp, int status, String json) throws IOException {
        resp.setStatus(status);
        resp.setContentType("application/json");
        resp.setCharacterEncoding("UTF-8");
        resp.getWriter().write(json);
    }
}
