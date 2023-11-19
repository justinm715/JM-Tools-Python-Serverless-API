import pypdf 
import pprint
import pandas as pd
from shapely.geometry import LineString, Polygon
from shapely.affinity import rotate
from collections import defaultdict


class AnnotationsExtractor:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        # Default scale factor assuming 1 inch = 72 points (72 DPI)
        self.scale_factor = 1
        self.pdf_reader = pypdf.PdfReader(open(self.pdf_path, 'rb'))

    @staticmethod
    def parse_scale_line_inches(scale_content, dpi=72):
        if not scale_content:
            return 1  # Default scale factor
        parts = scale_content.split("'-")
        feet = int(parts[0]) if parts[0] else 0
        inches = int(parts[1].replace('"', '').strip()
                     ) if len(parts) > 1 else 0
        total_inches = feet * 12 + inches
        return total_inches  # this is the number of inches the SCALE line is

    @staticmethod
    def parse_effective_seismic_weight_criteria(text):
        text = text.replace('\r', '\n').strip()
        sections = text.split('===')[1:]  # Splitting the text into sections
        parsed_data = {'Walls': {}, 'Floors': {}, 'Roofs': {}}

        for section in sections:
            lines = section.strip().split('\n')
            section_key = 'Roofs' if 'Roofs' in lines[0] else (
                'Floors' if 'Floors' in lines[0] else 'Walls')

            for line in lines[1:]:
                if line.startswith('R:') or line.startswith('F:') or line.startswith('W:'):
                    label = line.split(':')[1].strip()
                    current_dict = {}
                    parsed_data[section_key][label] = current_dict

                elif 'Weight:' in line:
                    current_dict['Weight'] = float(
                        line.split(':')[1].split()[0])

                elif 'Height:' in line:
                    current_dict['Height'] = float(
                        line.split(':')[1].split()[0])

                elif 'Snow:' in line:
                    current_dict['Snow'] = float(line.split(':')[1].split()[0])

        return parsed_data

    @staticmethod
    # coordinates given in feet
    def convert_to_real_world_coords_xy_pairs(coords, scale_factor):
        return [(float(coords[i]) * scale_factor / 12, float(coords[i + 1]) * scale_factor / 12) for i in range(0, len(coords), 2)]

    def get_number_of_pages(self):
        return len(self.pdf_reader.pages)

    def extract_real_world_coordinates(self, page_number):  # 0 is page 1
        if page_number < 0 or page_number >= len(self.pdf_reader.pages):
            return None

        page = self.pdf_reader.pages[page_number]
        annotations = page.get('/Annots')
        result = {"page_metadata": {
            "page_number": page_number + 1}, "annotations": []}

        # if page doesn't have annotations, skip it
        if not annotations:
            return None

        # go through the annotations to set the scale factor first before processing the rest
        # if there is no scale found, skip the page
        if annotations:
            resolved_annotations = annotations.get_object() if isinstance(
                annotations, pypdf.generic.IndirectObject) else annotations
            has_scale = False
            for annot_ref in resolved_annotations:
                annot = annot_ref.get_object()
                subject = annot.get('/Subj') or "None"
                contents = annot.get('/Contents') or "None"
                if subject == "SCALE":
                    linecoords = annot.get('/L')
                    pdf_unit_length = LineString([(linecoords[0], linecoords[1]),
                                                  (linecoords[2], linecoords[3])]).length
                    self.scale_factor = self.parse_scale_line_inches(
                        contents)/pdf_unit_length
                    has_scale = True
                    break
            if not has_scale:
                return None
        result['page_metadata']['scale_factor'] = self.scale_factor

        # process lines, polylines, polygons
        if annotations:
            resolved_annotations = annotations.get_object() if isinstance(
                annotations, pypdf.generic.IndirectObject) else annotations
            for annot_ref in resolved_annotations:
                annot = annot_ref.get_object()
                subtype = annot.get('/Subtype')
                subject = annot.get('/Subj') or "None"
                contents = annot.get('/Contents') or "None"
                rotation_deg = annot.get('/Rotation', 0)

                if subject == "SCALE":
                    continue

                if subtype in ['/Line', '/PolyLine', '/Polygon']:
                    coords = annot.get(
                        '/L') if subtype == '/Line' else annot.get('/Vertices')
                    real_world_coords = self.convert_to_real_world_coords_xy_pairs(
                        coords, self.scale_factor)
                    # account for rotations of polygons
                    # lines and polylines don't have a rotation
                    if subtype != '/Line' and rotation_deg != 0:
                        shape = Polygon(real_world_coords)
                        rotated_shape = rotate(
                            shape, -1*rotation_deg, origin='center')
                        # ignore the last coord. it's a repeat of the first
                        real_world_coords = list(
                            rotated_shape.exterior.coords[:-1])
                    result["annotations"].append({
                        "type": subtype[1:],
                        "subject": subject,
                        "contents": contents,
                        "coords": real_world_coords
                    })

        # get the effective seismic weight criteria
        if annotations:
            resolved_annotations = annotations.get_object() if isinstance(
                annotations, pypdf.generic.IndirectObject) else annotations
            for annot_ref in resolved_annotations:
                annot = annot_ref.get_object()
                subject = annot.get('/Subj') or "None"
                contents = annot.get('/Contents') or "None"
                if subject == "EFFECTIVE SEISMIC WEIGHT CRITERIA":
                    result['page_metadata']['weight_criteria'] = self.parse_effective_seismic_weight_criteria(
                        contents)
                    break

        return result

# # Example usage
# new_pdf_path = 'C.pdf'
# extractor = AnnotationsExtractor(new_pdf_path)

# pp = pprint.PrettyPrinter(indent=4)
# for page_num in range(extractor.get_number_of_pages()):
#     page_data = extractor.extract_real_world_coordinates(page_num)
#     pp.pprint(f"Page {page_num + 1} Data:")  # Pretty print the dictionary
#     pp.pprint(page_data)
#     # print(f"Page {page_num + 1} Data:")  # Pretty print the dictionary
#     # print(page_data)


class AreaElementAnalyzer:
    def __init__(self, data):
        self.data = data
        self.areas = []
        self.floors = []
        self.roofs = []
        self.walls = []
        self.process_data()

    def process_data(self):
        # Separate the annotations by their prefix
        for annotation in self.data.get('annotations', []):
            subject = annotation.get('subject', '')
            if ':' in subject:
                prefix, label = subject.split(': ')
                coords = [tuple(coord)
                          for coord in annotation.get('coords', [])]
                if prefix == 'A':
                    self.areas.append((label, Polygon(coords)))
                elif prefix == 'F':
                    self.floors.append((label, Polygon(coords)))
                elif prefix == 'R':
                    self.roofs.append((label, Polygon(coords)))
                elif prefix == 'W':
                    self.walls.append((label, LineString(coords)))

    def calculate_intersection_lengths(self):
        # Dictionary to store the calculated lengths and areas
        area_analysis = defaultdict(lambda: {'wall_lengths': defaultdict(
            float), 'floor_areas': defaultdict(float), 'roof_areas': defaultdict(float)})

        # Initialize all areas with all wall, floor, and roof types
        for area_label, _ in self.areas:
            for wall_label, _ in self.walls:
                area_analysis[area_label]['wall_lengths'][wall_label] = 0.0
            for floor_label, _ in self.floors:
                area_analysis[area_label]['floor_areas'][floor_label] = 0.0
            for roof_label, _ in self.roofs:
                area_analysis[area_label]['roof_areas'][roof_label] = 0.0

        # Calculating intersection lengths for each area with walls
        for area_label, area_polygon in self.areas:
            for wall_label, wall_line in self.walls:
                if area_polygon.intersects(wall_line):
                    intersection = area_polygon.intersection(wall_line)
                    area_analysis[area_label]['wall_lengths'][wall_label] += intersection.length

            for floor_label, floor_polygon in self.floors:
                if area_polygon.intersects(floor_polygon):
                    intersection = area_polygon.intersection(floor_polygon)
                    area_analysis[area_label]['floor_areas'][floor_label] += intersection.area

            for roof_label, roof_polygon in self.roofs:
                if area_polygon.intersects(roof_polygon):
                    intersection = area_polygon.intersection(roof_polygon)
                    area_analysis[area_label]['roof_areas'][roof_label] += intersection.area

        return area_analysis


class AreaAnalysisReport:
    def __init__(self, area_analysis, example_data):
        self.area_analysis = area_analysis
        self.example_data = example_data

    def generate_report(self):
        # Initialize a list to hold our DataFrame rows
        rows_list = []

        # Fetch the criteria details from example_data's weight_criteria
        weight_criteria = self.example_data['page_metadata']['weight_criteria']

        # Iterate over each region in the area analysis
        for region, analysis in self.area_analysis.items():
            # Process wall lengths
            for wall_label, length in analysis['wall_lengths'].items():
                wall_criteria = weight_criteria['Walls'][wall_label]
                rows_list.append({
                    'Region': region,
                    'Element Type': 'Wall',
                    'Element Label': wall_label,
                    'Height (ft)': wall_criteria['Height'],
                    'Weight (psf)': wall_criteria['Weight'],
                    # Snow weight is not applicable for walls
                    'Snow Weight (psf)': 0,
                    'Length (ft)': length,
                    'Area (sf)': 0,
                    'Total Weight (lbs)': length * wall_criteria['Height'] * wall_criteria['Weight']
                })

            # Process floor areas
            for floor_label, area in analysis['floor_areas'].items():
                floor_criteria = weight_criteria['Floors'][floor_label]
                rows_list.append({
                    'Region': region,
                    'Element Type': 'Floor',
                    'Element Label': floor_label,
                    'Height (ft)': 0,  # Height is not applicable for floors
                    'Weight (psf)': floor_criteria['Weight'],
                    # Snow weight is not applicable for floors
                    'Snow Weight (psf)': 0,
                    'Length (ft)': 0,
                    'Area (sf)': area,
                    'Total Weight (lbs)': area * floor_criteria['Weight']
                })

            # Process roof areas
            for roof_label, area in analysis['roof_areas'].items():
                roof_criteria = weight_criteria['Roofs'][roof_label]
                rows_list.append({
                    'Region': region,
                    'Element Type': 'Roof',
                    'Element Label': roof_label,
                    'Height (ft)': 0,  # Height is not applicable for roofs
                    'Weight (psf)': roof_criteria['Weight'],
                    'Snow Weight (psf)': roof_criteria['Snow'],
                    'Length (ft)': 0,
                    'Area (sf)': area,
                    'Total Weight (lbs)': area * (roof_criteria['Weight'] + roof_criteria['Snow'])
                })

        # Create a DataFrame
        report_df = pd.DataFrame(rows_list)

        # Define a custom sort order for the element types
        custom_sort_order = {'Roof': 1, 'Floor': 2, 'Wall': 3}

        # Add a sort key column based on custom sort order
        report_df['Sort Key'] = report_df['Element Type'].map(
            custom_sort_order)

        # Sort by Region and then by the custom sort key within each Region, and alphabetically within the subgroup
        report_df = report_df.sort_values(
            by=['Region', 'Sort Key', 'Element Label'])

        # Drop the 'Sort Key' column as it's no longer needed after sorting
        report_df.drop('Sort Key', axis=1, inplace=True)

        return report_df
