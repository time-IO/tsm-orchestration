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

    <Parameter override="false" name="ApiVersion" value="v1.0"/>
    <Parameter override="false" name="serviceRootUrl" value="{tomcat_proxy_url}{schema}"/>
    <Parameter override="false" name="defaultCount" value="false"/>
    <Parameter override="false" name="defaultTop" value="100"/>
    <Parameter override="false" name="maxTop" value="100000"/>
    <Parameter override="false" name="maxDataSize" value="25000000"/>

    <Parameter override="false" name="bus.busImplementationClass" 
        value="de.fraunhofer.iosb.ilt.frostserver.messagebus.InternalMessageBus"/>
    <Parameter override="false" name="bus.workerPoolSize" value="10"/>
    <Parameter override="false" name="bus.maxQueueSize" value="1000"/>

    <Parameter override="false" name="persistence.persistenceManagerImplementationClass" 
        value="de.fraunhofer.iosb.ilt.frostserver.persistence.pgjooq.imp.PostgresPersistenceManagerLong"/>
    <Parameter override="false" name="persistence.idGenerationMode" value="ServerGeneratedOnly"/>
    <Parameter override="false" name="persistence.autoUpdateDatabase" value="true"/>
    <Parameter override="false" name="persistence.alwaysOrderbyId" value="true"/>
    <Parameter override="false" name="persistence.db_jndi_datasource" value="jdbc/sensorThings"/>
    <Parameter override="false" name="persistence.queryTimeout" value="120"/>
    <Parameter override="false" name="persistence.slowQueryThreshold" value="500"/>

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
