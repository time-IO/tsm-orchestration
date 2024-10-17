ARG TOMCAT_IMAGE_TAG=9

FROM tomcat:${TOMCAT_IMAGE_TAG}

EXPOSE 8080

ARG UID=1000
ARG GID=1000
ARG FROST_URL=https://repo1.maven.org/maven2/de/fraunhofer/iosb/ilt/FROST-Server/FROST-Server.HTTP/2.4.2/FROST-Server.HTTP-2.4.2.war
ARG POSTGIS_JDBC_URL=https://repo1.maven.org/maven2/net/postgis/postgis-jdbc/2024.1.0/postgis-jdbc-2024.1.0.jar
ARG POSTGRESQL_URL=https://repo1.maven.org/maven2/org/postgresql/postgresql/42.7.4/postgresql-42.7.4.jar

# Create a tomcat user with the UID and GID specified in the build arguments
# If the UID is already in use, just print out the info
RUN mkdir -p $CATALINA_HOME/conf/Catalina/localhost \
    && apt-get update && apt-get install wget \
    && apt-get clean \
    && addgroup --system --gid ${GID} tomcat \
    && adduser --system --uid ${UID} --gid ${GID} --home /home/tomcat tomcat \
    || echo "The UID '${UID}' is already in use."\

# Download the FROST-Server.war, postgis-jdbc.jar, and postgresql.jar files
# Create the /share directory and set the owner to the UID user
RUN mkdir -p $CATALINA_HOME/conf/Catalina/localhost \
    && mkdir -p /share \
    && wget --show-progress=off -O $CATALINA_HOME/lib/postgis-jdbc.jar $POSTGIS_JDBC_URL \
    && wget --show-progress=off -O $CATALINA_HOME/lib/postgresql.jar $POSTGRESQL_URL \
    && wget --show-progress=off -O /share/FROST-Server.war $FROST_URL \
    && chown -R ${UID}:${GID} $CATALINA_HOME \
    && chown -R ${UID}:${GID} /share

# Add the root ca-certificates to the user's .postgresql directory
RUN mkdir ${HOME}/.postgresql \
    && cp /etc/ssl/certs/ca-certificates.crt ${HOME}/.postgresql/root.crt