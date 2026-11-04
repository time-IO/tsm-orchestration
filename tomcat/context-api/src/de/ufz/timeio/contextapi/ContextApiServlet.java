package de.ufz.timeio.contextapi;

import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.AtomicMoveNotSupportedException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.nio.file.attribute.PosixFilePermissions;
import java.security.MessageDigest;
import java.util.Arrays;
import java.util.List;
import java.util.regex.Pattern;
import java.util.stream.Collectors;
import java.util.stream.Stream;
import javax.xml.parsers.DocumentBuilderFactory;
import org.w3c.dom.Element;

/** Manages the Tomcat context descriptors of FROST instances: PUT/DELETE /contexts/{schema}, GET /contexts. */
public class ContextApiServlet extends HttpServlet {

    private static final int MAX_BODY = 64 * 1024;
    // No dots, slashes or '#' (Tomcat maps '#' in descriptor names to '/').
    private static final Pattern SCHEMA = Pattern.compile("[A-Za-z0-9_-]+");

    private final Object lock = new Object();
    private byte[] token;
    private Path contextDir;

    @Override
    public void init() {
        String t = System.getenv("FROST_CONTEXT_API_TOKEN");
        token = (t == null || t.isEmpty()) ? null : t.getBytes(StandardCharsets.UTF_8);
        contextDir = Path.of(System.getProperty("catalina.base"), "conf", "Catalina", "localhost")
                .toAbsolutePath().normalize();
    }

    @Override
    protected void service(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException {
        if (token == null) {
            reply(resp, 503, "{\"error\":\"FROST_CONTEXT_API_TOKEN is not configured\"}");
        } else if (!authorized(req)) {
            resp.setHeader("WWW-Authenticate", "Bearer");
            reply(resp, 401, "{\"error\":\"unauthorized\"}");
        } else {
            super.service(req, resp);
        }
    }

    @Override
    protected void doGet(HttpServletRequest req, HttpServletResponse resp) throws IOException {
        if (req.getPathInfo() != null && !req.getPathInfo().equals("/")) {
            reply(resp, 404, "{\"error\":\"not found\"}");
            return;
        }
        try (Stream<Path> files = Files.list(contextDir)) {
            List<String> names = files.map(p -> p.getFileName().toString())
                    .filter(n -> n.endsWith(".xml"))
                    .map(n -> n.substring(0, n.length() - 4))
                    .filter(n -> SCHEMA.matcher(n).matches())
                    .sorted()
                    .toList();
            reply(resp, 200, names.stream().map(n -> "\"" + n + "\"").collect(Collectors.joining(",", "[", "]")));
        }
    }

    @Override
    protected void doPut(HttpServletRequest req, HttpServletResponse resp) throws IOException {
        String schema = schemaOf(req);
        if (schema == null) {
            reply(resp, 400, "{\"error\":\"invalid schema name\"}");
            return;
        }
        byte[] body = req.getInputStream().readNBytes(MAX_BODY + 1);
        if (body.length > MAX_BODY) {
            reply(resp, 413, "{\"error\":\"body too large\"}");
            return;
        }
        // Keeps a working context from being replaced by garbage.
        if (!isContextXml(body)) {
            reply(resp, 400, "{\"error\":\"body must be a <Context> XML document\"}");
            return;
        }
        boolean changed;
        synchronized (lock) {
            changed = write(contextDir.resolve(schema + ".xml"), body);
        }
        reply(resp, 200, "{\"changed\":" + changed + "}");
    }

    @Override
    protected void doDelete(HttpServletRequest req, HttpServletResponse resp) throws IOException {
        String schema = schemaOf(req);
        if (schema == null) {
            reply(resp, 400, "{\"error\":\"invalid schema name\"}");
            return;
        }
        boolean existed;
        synchronized (lock) {
            existed = Files.deleteIfExists(contextDir.resolve(schema + ".xml"));
        }
        reply(resp, 200, "{\"changed\":" + existed + "}");
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
        return SCHEMA.matcher(schema).matches() ? schema : null;
    }

    /** Writes via temp file and atomic move; returns false if the content is unchanged. */
    private boolean write(Path target, byte[] content) throws IOException {
        // Rewriting identical content would make Tomcat redeploy the context.
        if (Files.exists(target) && Arrays.equals(Files.readAllBytes(target), content)) {
            return false;
        }
        // Not a *.xml name, so Tomcat's auto-deploy ignores it.
        Path tmp = Files.createTempFile(contextDir, ".tmp-", ".part",
                PosixFilePermissions.asFileAttribute(PosixFilePermissions.fromString("rw-------")));
        try {
            Files.write(tmp, content);
            try {
                Files.move(tmp, target, StandardCopyOption.ATOMIC_MOVE);
            } catch (AtomicMoveNotSupportedException e) {
                Files.move(tmp, target, StandardCopyOption.REPLACE_EXISTING);
            }
        } finally {
            Files.deleteIfExists(tmp);
        }
        return true;
    }

    private static boolean isContextXml(byte[] xml) {
        try {
            DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
            factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
            Element root = factory.newDocumentBuilder().parse(new ByteArrayInputStream(xml)).getDocumentElement();
            return root.getTagName().equals("Context");
        } catch (Exception e) {
            return false;
        }
    }

    private static void reply(HttpServletResponse resp, int status, String json) throws IOException {
        resp.setStatus(status);
        resp.setContentType("application/json");
        resp.setCharacterEncoding("UTF-8");
        resp.getWriter().write(json);
    }
}
