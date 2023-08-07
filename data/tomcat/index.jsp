<!DOCTYPE html>
<html>
    <head>
        <meta charset="UTF-8">
        <title>TSM FROST-Server</title>
    </head>
    <body>
        <ul>
            <%
                String webappsDir = "/usr/local/tomcat/webapps/";
                String scheme = request.getScheme();
                String serverName = request.getServerName();
                int serverPort = request.getServerPort();
                java.io.File[] webapps = new java.io.File(webappsDir).listFiles();
                for (java.io.File webapp : webapps) {
                    if (webapp.isDirectory() && !webapp.getName().equals("ROOT")) {
                        String webappName = webapp.getName();
                        String webappURL = scheme + "://" + serverName + ":" + serverPort + "/sta/" + webappName;
            %>
            <li><a href="<%=webappURL%>"><%=webappName%></a></li>
            <%
                    }
                }
            %>
        </ul>
    </body>
</html>
