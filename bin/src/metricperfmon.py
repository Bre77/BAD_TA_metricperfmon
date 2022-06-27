import sys, os, subprocess, json
from xml.etree.ElementTree import fromstring, tostring

SCHEME = """<scheme>
    <title>Local performance monitoring</title>
    <description>Collect performance data from the local machine.</description>
    <use_single_instance>true</use_single_instance>
    <streaming_mode>xml</streaming_mode>
    <endpoint>
        <id>win-perfmon</id>
        <args>
            <arg name="name">
                <title>name</title>
            </arg>
            <arg name="counters">
                <title>counters</title>
                <list_delimiter>;</list_delimiter>
                <required_on_create>false</required_on_create>
            </arg>
            <arg name="nonmetric_counters">
                <title>nonmetric_counters</title>
                <list_delimiter>;</list_delimiter>
                <required_on_create>false</required_on_create>
            </arg>
            <arg name="instances">
                <title>instances</title>
                <list_delimiter>;</list_delimiter>
                <required_on_create>false</required_on_create>
            </arg>
            <arg name="interval">
                <validation>is_pos_int('interval')</validation>
                <title>interval</title>
                <required_on_create>false</required_on_create>
                <data_type>number</data_type>
            </arg>
            <arg name="object">
                <title>object</title>
                <required_on_create>false</required_on_create>
            </arg>
            <arg name="showZeroValue">
                <title>showZeroValue</title>
                <required_on_create>false</required_on_create>
                <required_on_edit>false</required_on_edit>
            </arg>
            <arg name="mode">
                <title>mode</title>
                <required_on_create>false</required_on_create>
                <required_on_edit>false</required_on_edit>
            </arg>
            <arg name="samplingInterval">
                <title>samplingInterval</title>
                <required_on_create>false</required_on_create>
                <required_on_edit>false</required_on_edit>
            </arg>
            <arg name="stats">
                <title>stats</title>
                <required_on_create>false</required_on_create>
                <required_on_edit>false</required_on_edit>
            </arg>
            <arg name="useEnglishOnly">
                <title>useEnglishOnly</title>
                <required_on_create>false</required_on_create>
                <required_on_edit>false</required_on_edit>
            </arg>
            <arg name="useWinApiProcStats">
                <title>useWinApiProcStats</title>
                <required_on_create>false</required_on_create>
                <required_on_edit>false</required_on_edit>
            </arg>
            <arg name="formatString">
                <title>formatString</title>
                <required_on_create>false</required_on_create>
                <required_on_edit>false</required_on_edit>
            </arg>
            <arg name="usePDHFmtNoCap100">
                <title>usePDHFmtNoCap100</title>
                <required_on_create>false</required_on_create>
                <required_on_edit>false</required_on_edit>
            </arg>
        </args>
    </endpoint>
</scheme>"""

if len(sys.argv) > 1:
    if sys.argv[1] == "--scheme":
        print(SCHEME)
    elif sys.argv[1] == "--validate-arguments":
        pass
    else:
        pass
else:
    if not os.environ['SPLUNK_HOME']:
        raise("SPLUNK_HOME not set")
    process = subprocess.Popen(os.environ['SPLUNK_HOME']+"/bin/splunk-perfmon.exe", stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=sys.stdin, text=True)

    if process.stdout.readline().rstrip('\n') == "<stream>":
        print("<stream>")

    while True:
        xml = ""
        while True:
            line = process.stdout.readline()
            xml += line
            if line.startswith("</event>"):
                break
        orig_event = fromstring(xml)
        orig_event.attrib['stanza'] = "metric"+orig_event.attrib['stanza']

        data_element = orig_event.find('data')
        data_lines = data_element.text.split('\n')
        
        fields = False
        for line in data_lines:
            if line.startswith("instance"):
                # Get fields from header
                fields = line.rstrip('\t').split('\t')
                for x in range(1,len(fields)):
                    fields[x] = "metric_name:"+fields[x]
                continue
            if not fields:
                continue
            # Have fields, get values
            values = line.rstrip('\t').split('\t')
            raw = {}
            for field,value in zip(fields,values):
                if field != "instance":
                    if "e" in value: # Cannot handle this format
                        pass
                    value = float(value)
                    # Remove decimals if all zeros
                    if value % 1 == 0:
                        value = int(value)
                raw[field] = value
            data_element.text = json.dumps(raw,separators=(',', ':'))
            print(tostring(orig_event).decode())