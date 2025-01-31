from extract_xml import ExtractXML  # Import the class

# Create an instance of ExtractXML
extractor = ExtractXML()

# Use the method to extract BaseURL tags from an XML file
xml_file = "/workspaces/pydash/client/foo"  # Replace with your actual XML file path
base_urls = extractor.extract_base_urls(xml_file)

# Print extracted URLs
for url in base_urls:
    print(url)