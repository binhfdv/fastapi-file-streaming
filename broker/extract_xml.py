import xml.etree.ElementTree as ET

class ExtractXML():
    def __init__(self, tag: str = "BaseURL"):
        self.tag = tag


    def extract_base_urls(self, xml_file):
        tree = ET.parse(xml_file)
        root = tree.getroot()

        base_urls = [elem.text.strip() for elem in root.findall(str(".//"+self.tag))]
        
        return base_urls

