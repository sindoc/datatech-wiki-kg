<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="2.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:output method="xml" encoding="UTF-8" omit-xml-declaration="yes"/>

  <xsl:template match="/userpage">
    <page>
      <xsl:text>{{User page}}&#10;&#10;</xsl:text>
      <xsl:apply-templates select="lead/para"/>
      <xsl:apply-templates select="section"/>
    </page>
  </xsl:template>

  <xsl:template match="lead/para">
    <xsl:apply-templates select="node()" mode="inline"/>
    <xsl:text>&#10;&#10;</xsl:text>
  </xsl:template>

  <xsl:template match="section">
    <xsl:text>== </xsl:text>
    <xsl:value-of select="@title"/>
    <xsl:text> ==&#10;&#10;</xsl:text>
    <xsl:apply-templates select="para"/>
    <xsl:apply-templates select="list"/>
  </xsl:template>

  <xsl:template match="section/para">
    <xsl:apply-templates select="node()" mode="inline"/>
    <xsl:text>&#10;&#10;</xsl:text>
  </xsl:template>

  <xsl:template match="list">
    <xsl:apply-templates select="item"/>
    <xsl:text>&#10;</xsl:text>
  </xsl:template>

  <xsl:template match="item">
    <xsl:text>* </xsl:text>
    <xsl:choose>
      <xsl:when test="@href">
        <xsl:text>[</xsl:text>
        <xsl:value-of select="@href"/>
        <xsl:text> </xsl:text>
        <xsl:apply-templates select="node()" mode="inline"/>
        <xsl:text>]</xsl:text>
      </xsl:when>
      <xsl:otherwise>
        <xsl:apply-templates select="node()" mode="inline"/>
      </xsl:otherwise>
    </xsl:choose>
    <xsl:text>&#10;</xsl:text>
  </xsl:template>

  <xsl:template match="strong" mode="inline">
    <xsl:text>'''</xsl:text>
    <xsl:apply-templates select="node()" mode="inline"/>
    <xsl:text>'''</xsl:text>
  </xsl:template>

  <xsl:template match="text()" mode="inline">
    <xsl:value-of select="."/>
  </xsl:template>

</xsl:stylesheet>
