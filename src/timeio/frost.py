#!/usr/bin/env python3
from __future__ import annotations

import logging
import pathlib
import xml.etree.ElementTree as ET  # noqa
from urllib.parse import urlparse, urlunparse

from timeio.crypto import decrypt, get_crypt_key

logger = logging.getLogger(__name__)

_TEMPLATE = """\
<?xml version="1.0" encoding="UTF-8"?>
<Context path="/{schema}" docBase="/share/FROST-Server.war">

    <Parameter override="false" name="ApiVersion" value="v1.0" description="The version tag of the API used in the URL."/>
    <Parameter override="false" name="serviceRootUrl" value="{tomcat_proxy_url}{schema}" description="The base URL of the SensorThings Server without version."/>
    <Parameter override="false" name="defaultCount" value="false" description="The default value for the $count query option."/>
    <Parameter override="false" name="defaultTop" value="100" description="The default value for the $top query option."/>
    <Parameter override="false" name="maxTop" value="100000" description="The maximum allowed value for the $top query option."/>
    <Parameter override="false" name="maxDataSize" value="25000000" description="The maximum allowed estimated data size (in bytes) for responses."/>

    <Parameter override="false" name="bus.busImplementationClass" 
        value="de.fraunhofer.iosb.ilt.frostserver.messagebus.InternalMessageBus" description="The java class used for connecting to the message bus."/>
    <Parameter override="false" name="bus.workerPoolSize" value="10"/>
    <Parameter override="false" name="bus.maxQueueSize" value="1000"/>

    <Parameter override="false" name="persistence.persistenceManagerImplementationClass" 
        value="de.fraunhofer.iosb.ilt.frostserver.persistence.pgjooq.imp.PostgresPersistenceManagerLong" description="The java class used for persistence (must implement PersistenceManaher interface)"/>
    <Parameter override="false" name="persistence.idGenerationMode" value="ServerGeneratedOnly" description="Mode for id generation when using PostgresPersistenceManagerString."/>
    <Parameter override="false" name="persistence.autoUpdateDatabase" value="false" description="Automatically apply database updates."/>
    <Parameter override="false" name="persistence.alwaysOrderbyId" value="true" description="Always add an 'orderby=id asc' to queries to ensure consistent paging."/>
    <Parameter override="false" name="persistence.db_jndi_datasource" value="jdbc/sensorThings" description="JNDI data source name"/>
    <Parameter override="false" name="persistence.queryTimeout" value="120" description="The maximum duration, in seconds, that a query is allowed to take."/>
    <Parameter override="false" name="persistence.slowQueryThreshold" value="500" description="Toggle indicating whether the OpenAPI plugin should be enabled." />

    <Parameter override="false" name="plugins.openApi.enable" value="true"/>

    <Resource
        name="jdbc/sensorThings" auth="Container"
        type="javax.sql.DataSource" 
        driverClassName="org.postgresql.Driver"
        url="jdbc:{db_url}"
        username="{username}" 
        password="{password}"

        maxTotal="20" 
        maxIdle="10" 
        minIdle="5" 
        initialSize="5"
        maxWaitMillis="10000"

        testOnBorrow="true"
        testWhileIdle="true"
        validationQuery="SELECT 1"
        validationQueryTimeout="5"
        timeBetweenEvictionRunsMillis="30000"
        minEvictableIdleTimeMillis="60000"
        numTestsPerEvictionRun="3"

        removeAbandonedOnBorrow="true"
        removeAbandonedOnMaintenance="true"
        removeAbandonedTimeout="300"
        logAbandoned="true"

        defaultAutoCommit="false"
        connectionProperties="socketTimeout=30;loginTimeout=10;tcpKeepAlive=true;ApplicationName=FROST-Server-{schema};prepareThreshold=3;preparedStatementCacheQueries=256;preparedStatementCacheSizeMiB=5;defaultRowFetchSize=100;reWriteBatchedInserts=true"
    />
</Context>
"""
CONTEXT_FILES_DIR = (
    # tsm-orchestration/src/frost_context_files
    pathlib.Path(__file__)
    .resolve()
    .parent.parent.joinpath("frost_context_files")
)


def write_context_file(schema, user, password, db_url, tomcat_proxy_url) -> None:
    parts = urlparse(db_url)
    hostname = parts.hostname
    if parts.port:
        hostname += f":{parts.port}"
    jdbc_url = urlunparse((parts.scheme, hostname, parts.path, "", "", ""))
    content = _TEMPLATE.format(
        db_url=jdbc_url,
        schema=schema,
        username=user,
        password=decrypt(password, get_crypt_key()),
        tomcat_proxy_url=tomcat_proxy_url,
    ).strip()

    path = f"{CONTEXT_FILES_DIR}/{schema}.xml"
    logger.debug(f"write tomcat context file {path!r}")
    with open(path, "wb") as fh:
        fh.write(ET.tostring(ET.XML(content)))
