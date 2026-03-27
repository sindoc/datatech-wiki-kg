<?xml version="1.0" encoding="UTF-8"?>
<p:declare-step name="render-navbox"
                xmlns:p="http://www.w3.org/ns/xproc"
                version="1.0">

  <p:output port="result"/>

  <p:option name="source" required="true"/>
  <p:option name="stylesheet" required="true"/>
  <p:option name="output" required="true"/>

  <p:load name="source-doc">
    <p:with-option name="href" select="concat('file://', $source)"/>
  </p:load>

  <p:load name="stylesheet-doc">
    <p:with-option name="href" select="concat('file://', $stylesheet)"/>
  </p:load>

  <p:xslt name="transform">
    <p:input port="source">
      <p:pipe step="source-doc" port="result"/>
    </p:input>
    <p:input port="stylesheet">
      <p:pipe step="stylesheet-doc" port="result"/>
    </p:input>
    <p:input port="parameters">
      <p:empty/>
    </p:input>
  </p:xslt>

  <p:store method="text" name="store-output">
    <p:input port="source">
      <p:pipe step="transform" port="result"/>
    </p:input>
    <p:with-option name="href" select="concat('file://', $output)"/>
  </p:store>

  <p:identity>
    <p:input port="source">
      <p:pipe step="transform" port="result"/>
    </p:input>
  </p:identity>

</p:declare-step>
