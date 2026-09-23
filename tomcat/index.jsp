<%@ page contentType="application/json; charset=UTF-8" session="false" trimDirectiveWhitespaces="true" %>
<%@ page import="java.io.File" %>
<%@ page import="java.util.Arrays" %>
<%!
    private static String esc(String s) {
        StringBuilder sb = new StringBuilder(s.length() + 8);
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            switch (c) {
                case '"':  sb.append("\\\""); break;
                case '\\': sb.append("\\\\"); break;
                case '\n': sb.append("\\n");  break;
                case '\r': sb.append("\\r");  break;
                case '\t': sb.append("\\t");  break;
                default:
                    if (c < 0x20) sb.append(String.format("\\u%04x", (int) c));
                    else sb.append(c);
            }
        }
        return sb.toString();
    }
%>
<%
    out.clearBuffer();

    response.setHeader("Access-Control-Allow-Origin", "*");
    response.setHeader("Cache-Control", "no-cache, no-store");

    final String webappsDir = "/usr/local/tomcat/webapps/";

    File[] webapps = new File(webappsDir).listFiles();
    if (webapps == null) {
        webapps = new File[0];   // Verzeichnis fehlt / nicht lesbar
    }
    Arrays.sort(webapps);

    String base = String.format("%s://%s:%d",
        request.getScheme(), request.getServerName(), request.getServerPort());

    StringBuilder sb = new StringBuilder("{\"endpoints\":[");
    boolean first = true;

    for (File webapp : webapps) {
        if (!webapp.isDirectory() || "ROOT".equals(webapp.getName())) {
            continue;
        }

        String name = webapp.getName();

        int i1 = name.indexOf('_');
        int i2 = (i1 < 0) ? -1 : name.indexOf('_', i1 + 1);
        String group   = (i1 < 0) ? name : name.substring(0, i1);
        String project = (i2 < 0) ? null : name.substring(i1 + 1, i2);
        String display = (project == null) ? group : group + " " + project;

        if (!first) sb.append(',');
        first = false;

        sb.append("{\"name\":\"").append(esc(name)).append('"')
          .append(",\"displayName\":\"").append(esc(display)).append('"')
          .append(",\"group\":\"").append(esc(group)).append('"')
          .append(",\"project\":")
          .append(project == null ? "null" : "\"" + esc(project) + "\"")
          .append(",\"url\":\"").append(esc(base + "/sta/" + name + "/v1.1")).append("\"}");
    }

    sb.append("]}");
    out.print(sb);
%>