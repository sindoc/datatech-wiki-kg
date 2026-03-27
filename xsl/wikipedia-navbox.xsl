<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="2.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:output method="xml" encoding="UTF-8" omit-xml-declaration="yes"/>

  <xsl:template match="/navbox">
    <page>
      <xsl:text>{{Navbox&#10;</xsl:text>
      <xsl:text>| name = </xsl:text>
      <xsl:value-of select="@name"/>
      <xsl:text>&#10;</xsl:text>
      <xsl:text>| title = </xsl:text>
      <xsl:value-of select="@title"/>
      <xsl:text>&#10;</xsl:text>
      <xsl:text>| state = </xsl:text>
      <xsl:value-of select="@state"/>
      <xsl:text>&#10;</xsl:text>
      <xsl:text>| listclass = </xsl:text>
      <xsl:value-of select="@listclass"/>
      <xsl:text>&#10;</xsl:text>
      <xsl:for-each select="row">
        <xsl:variable name="idx" select="position()"/>
        <xsl:text>| group</xsl:text>
        <xsl:value-of select="$idx"/>
        <xsl:text> = </xsl:text>
        <xsl:value-of select="@group"/>
        <xsl:text>&#10;</xsl:text>
        <xsl:text>| list</xsl:text>
        <xsl:value-of select="$idx"/>
        <xsl:text> =&#10;</xsl:text>
        <xsl:apply-templates select="item" mode="list"/>
        <xsl:text>&#10;</xsl:text>
      </xsl:for-each>
      <xsl:text>}}</xsl:text>
    </page>
  </xsl:template>

  <xsl:template match="item" mode="list">
    <xsl:param name="depth" select="1"/>
    <xsl:value-of select="string-join(for $i in 1 to $depth return '*', '')"/>
    <xsl:text> </xsl:text>
    <xsl:choose>
      <xsl:when test="@raw">
        <xsl:value-of select="@raw"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:text>[[</xsl:text>
        <xsl:value-of select="@target"/>
        <xsl:if test="@label">
          <xsl:text>|</xsl:text>
          <xsl:value-of select="@label"/>
        </xsl:if>
        <xsl:text>]]</xsl:text>
      </xsl:otherwise>
    </xsl:choose>
    <xsl:text>&#10;</xsl:text>
    <xsl:apply-templates select="item" mode="list">
      <xsl:with-param name="depth" select="$depth + 1"/>
    </xsl:apply-templates>
  </xsl:template>

</xsl:stylesheet>
