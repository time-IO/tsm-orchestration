FROM tomcat:9-jdk17

EXPOSE 8080

ARG UID=1000
ARG GID=1000
ARG FROST_URL=https://repo1.maven.org/maven2/de/fraunhofer/iosb/ilt/FROST-Server/FROST-Server.HTTP/2.1.2/FROST-Server.HTTP-2.1.2.war
ARG POSTGIS_JDBC_URL=https://repo1.maven.org/maven2/net/postgis/postgis-jdbc/2.5.1/postgis-jdbc-2.5.1.jar
ARG POSTGRESQL_URL=https://repo1.maven.org/maven2/org/postgresql/postgresql/42.5.4/postgresql-42.5.4.jar

COPY index.jsp $CATALINA_HOME/webapps/ROOT/index.jsp

RUN mkdir -p $CATALINA_HOME/conf/Catalina/localhost \
    && apt-get update && apt-get install wget \
    && apt-get clean \
    && addgroup --system --gid ${GID} tomcat \
    && adduser --system --uid ${UID} --gid ${GID} tomcat \
    && mkdir -p $CATALINA_HOME/conf/Catalina/localhost \
    && wget -O $CATALINA_HOME/lib/postgis-jdbc.jar $POSTGIS_JDBC_URL \
    && wget -O $CATALINA_HOME/lib/postgresql.jar $POSTGRESQL_URL \    
    && chown -R tomcat:tomcat $CATALINA_HOME \
    && mkdir -p /share \
    && wget -O /share/FROST-Server.war $FROST_URL \
    && chown -R tomcat /share

USER tomcat
