import boto3
import time
from quantulum3 import parser
import pint
from normalize_test import driver


class UnitQuantity:
    def __init__(self, value, unit, entity):
        self.value = value
        self.unit = unit
        self.entity = entity

    def __repr__(self):
        return "(" + str(self.value) + ", " + self.unit + ", " + self.entity + ")"


def parse_product_dict(products, unit_preferences):
    '''
    input: 
    products = { category : 
        [
            [store1_product_name, ...], 
            [store2_product_name, ...], 
            ...
        ], 
        ...
    }
    unit_preferences = {'entity' : 'preferred_unit', ...}

    output: 
    { category :
        [
            [(store1_product_name, [UnitQuantity, ...]), ...], 
            [(store2_product_name, [UnitQuantity, ...]), ...], 
            ...
        ],
        ...
    }

    UnitQuantity
    + value : float
    + unit : str
    + entity : str

    Takes in a dict/list structure that contains product descriptions and a dict of unit preferences to define which
        unit to convert to for each "entity" (category of unit; ex: mass, length). 
    Parses each product description to find quantities within them. If found, will attempt to extract the
        magnitude and unit of the quantity and convert them to a unit in unit preferences. If no preferred unit is found for a quantity's
        entity, then that unit becomes the preferred unit for that entity to ensure all entities convert to the same unit.
        This means that the input unit_preferences variable is updated in the process.
    '''
    # --- for testing ---
    # products = driver('description') 
    # unit_preferences = {
    #     'mass':'g',
    #     'length':'m'
    # }
    # --------------------
    ureg = pint.UnitRegistry()
    output_dict = {}
    for category in products.keys():
        product_list = products[category]
        parsed_product_list = []
        for store_product_desc in product_list:
            parsed_store_list = []
            for product_desc in store_product_desc:
                # NOTE: for ranges (ex: "USDA Choice Top Sirloin Steak - 1.18-2.24 lbs"), it averages the two numbers
                quantities = parser.parse(product_desc)
                converted_quantity_objects = []
                for i, quan in enumerate(quantities):
                    quantity_obj = convert_units(quan, unit_preferences)
                    converted_quantity_objects.append(quantity_obj)
                parsed_store_list.append((product_desc, converted_quantity_objects))
            parsed_product_list.append(parsed_store_list)
        output_dict[category] = parsed_product_list
    return output_dict


def convert_units(quantity, unit_preferences):
    ureg = pint.UnitRegistry()
    value = quantity.value
    unit = quantity.unit.name
    entity_name = quantity.unit.entity.name
    if entity_name == "dimensionless":
        return UnitQuantity(value, unit, entity_name)
    try:
        pint_obj = value * ureg(unit)
    except pint.errors.DimensionalityError:    
        # for when quantulum3 returns a weird unit ureg can't parse (ex: pound-mass)
        # if this causes any errors, it might be a good idea to have a custom map from quantulum3 units
        #   to pint units (See references at bottom)
        pint_obj = value * ureg(extract_unit(quantity.surface))
    except Exception as e:
        raise Exception(e, quantity)

    pref = None
    if entity_name in unit_preferences:
        pref = unit_preferences[entity_name]
    else:
        # new preference, so we assume that is the preferred unit
        unit_preferences[entity_name] = unit
        return UnitQuantity(pint_obj.magnitude, unit, entity_name)
    pint_obj = pint_obj.to(pref)
    return UnitQuantity(pint_obj.magnitude, pref, entity_name)


def extract_unit(surface_string):
    '''
    Takes in the raw string that was used to discover a quantity, returns the unit

    Assumptions: unit is the last word in a space-separated string
    NOTE: Treating this as a separate function despite its simplicity to manage outliers later
    '''
    return surface_string.split(" ")[-1]


'''
quantulum3 units: https://github.com/nielstron/quantulum3/blob/dev/quantulum3/units.json
quantulum3 entities: https://github.com/nielstron/quantulum3/blob/dev/quantulum3/entities.json

pint units: https://github.com/hgrecco/pint/blob/master/pint/default_en.txt
    deciphering and altering unit text file: https://pint.readthedocs.io/en/stable/defining.html
'''
# quantulum3 simple entity list for reference
entity_list = [
    "dimensionless",
    "length",
    "mass",
    "currency",
    "time",
    "temperature",
    "charge",
    "angle",
    "data storage",
    "amount of substance",
    "catalytic activity",
    "area",
    "volume",
    "volume (lumber)",
    "force",
    "pressure",
    "energy",
    "power",
    "speed",
    "acceleration",
    "fuel economy",
    "fuel consumption",
    "angular speed",
    "angular acceleration",
    "density",
    "specific volume",
    "moment of inertia",
    "torque",
    "thermal resistance",
    "thermal conductivity",
    "specific heat capacity",
    "volumetric flow",
    "mass flow",
    "concentration",
    "dynamic viscosity",
    "kinematic viscosity",
    "fluidity",
    "surface tension",
    "permeability",
    "sound level",
    "luminous intensity",
    "luminous flux",
    "illuminance",
    "luminance",
    "typographical element",
    "image resolution",
    "frequency",
    "instance frequency",
    "flux density",
    "linear mass density",
    "linear charge density",
    "surface charge density",
    "charge density",
    "current",
    "linear current density",
    "surface current density",
    "electric potential",
    "electric field",
    "electrical resistance",
    "electrical resistivity",
    "electrical conductance",
    "electrical conductivity",
    "capacitance",
    "inductance",
    "magnetic flux",
    "reluctance",
    "magnetomotive force",
    "magnetic field",
    "irradiance",
    "radiation absorbed dose",
    "radioactivity",
    "radiation exposure",
    "radiation",
    "data transfer rate"
]

#  for testing:
# if __name__=="__main__":
#     print(parse_product_dict({}, {}))



'''
Past code dealing with the database directly:


def parse_quantities(quantity_list):
    # Takes in a list of elements of form (productname:str, [quantity:quantulum3QuantityType, ...])    

    ureg = pint.UnitRegistry() 
    # can set the default_system to "mks" for metric system default: ureg.default_system = 'mks'

    # groups products by entity
    quantity_map = {}
    for quantity in quantity_list: # quantity = [name, QuantityType]
        name = quantity[0]
        quan = quantity[1]
        value = quan.value
        unit = quan.unit.name
        entity_name = quan.unit.entity.name
        try:
            pint_obj = value * ureg(unit)
        except pint.errors.DimensionalityError: # for when quantulum3 returns a weird unit ureg can't parse (ex: pound-mass)
            pint_obj = ureg(quan.surface)
        except Exception as e:
            print(e)
            continue
        if entity_name in quantity_map:
            product_list = quantity_map[entity_name]
            product_list.append((name, pint_obj))
            quantity_map[entity_name] = product_list
        else:
            quantity_map[entity_name] = [(name, pint_obj)]

    # converts all products within one entity to one unit
    for entity in quantity_map.keys():
        product_list = quantity_map[entity]
        if len(product_list) < 1:
            print("empty product list for entity:", entity)
        if entity in unit_preferences:
            standard_entity_unit = unit_preferences[entity]
        else:
            standard_entity_unit = product_list[0][1].units
        converted_product_list = []
        for product in product_list:
            converted_product = (product[0], product[1].to(standard_entity_unit))
            # print(converted_product)
            converted_product_list.append(converted_product)

        # sorts entity product list my magnitude
        converted_product_list.sort(key=lambda x:x[1].magnitude)
        #print('here:', converted_product_list)
        quantity_map[entity] = converted_product_list
    
    for entity in quantity_map.keys():
        print("------------------------------------")
        print(entity)
        print("------------------------------------")
        product_list = quantity_map[entity]
        for product in product_list:
            print(f'{product[0]}: {product[1]}')

        # if quantity[1].unit.entity in quantity_map:
        #     quantity_map[quantity[1].unit.entity] = [quantity]
        # else:
        #     entity_list = quantity_map[quantity[1].unit.entity]
        #     entity_list.append(quantity)
        #     quantity_map[quantity[1].unit.entity] = entity_list
    
    #for key in quantity_map.keys():



        # if "cent" in quantities[0].unit.name:
        #     metric = ureg(str(quantities[0].value * 100) + " * " + quantities[0].unit.name.replace("cent", "currency"))
        # else:
        #     print(quantities[0].unit.name)


#def quantity_to_pint_ureg

def main(table):
    # parse_quantities([])
    parse_product_dict({})    
    return
    table_list = table.scan(Select='ALL_ATTRIBUTES')["Items"]
    all_product_sizes = []
    for row in table_list:
        query = row['query']
        category = row['category']
        product = row['product']
        for store in row['stores'].keys():
            if store=='vendor1':
                continue
                parse_vendor1(row['stores'][store])
            elif store=='vendor2':
                continue
                parse_vendor2(row['stores'][store])
            elif store=='vendor3':
                product_sizes = parse_vendor3(row['stores'][store])
                all_product_sizes.append(product_sizes)
            else:
                print('Unhandled store', store)
        #print(query, category, product)
    for query_product_sizes in all_product_sizes:
        parse_quantities(query_product_sizes)
        # for product_size in query_product_sizes:
        #     print(product_size)
    return

def parse_vendor1(vendor1):
    
    #vendor1 is a list of products
    #vendor1[0]['info']['name'] USUALLY contains weight at the end
    #    ex: 
    #        Great Value Whole Milk, 1 Gallon, 128 Fl. Oz.
    #        Great Value 2% Reduced-Fat Milk, 128 fl oz
    #    but sometimes the weight will be for individual packages, this seems to be if the count is after the weight
    #        ex:
    #            Popchips Variety Pack, 0.8 oz, 30 Count
    #vendor1[0]['info']['pricing']['displayPrice'] is the price
    #vendor1[0]['info']['pricing']['displayUnitPrice'] is a string that contains a price rate often with weight
    
    for product in vendor1:
        try:
            name = product['info']['name']
            price = product['info']['pricing']['displayPrice']
            unitPrice = product['info']['pricing']['displayUnitPrice']
        except Exception as e:
            print("Error parsing vendor1 product: ", e)
            continue
        # parsing name
        name_quantities = parser.parse(name)
        name_size = None
        count_seen, count = False, 0
        for quant in name_quantities:
            if quant.entity == "mass":
                if count_seen:
                    return #
            elif quant.entity == "count":
                count = quant.value
                count_seen = True
            

def parse_vendor2(vendor2):
    # vendor2 is a list of products
    # vendor2[0]['info']['product_description']['bullet_descriptions'] is a list of specs
    # each spec seems to have the form "<B>Spec Name</B> Spec Value (with unit)"

    for product in vendor2:
        pass

def parse_vendor3(vendor3):
    # vendor3 is a list of products
    # vendor3[0]['name'] is the name, sometimes contains weight
    # when vendor3[0]['specifications'][x]['name']['size'] exists
    #     then vendor3[0]['specifications'][x]['name']['value'] contains the weight
    #     in the form of a string that can be parsed with 
    product_sizes = []
    products_with_sizes = 0
    total_products = 0
    for product in vendor3:
        size = None
        try:
            name = product['name']
            specs = product['specifications']
            size_seen = False
            for spec in specs:
                if spec['name'] is not None and spec['name'].lower()=='size':
                    size_seen = True
                    sizes = parser.parse(spec['value'])
                    if len(sizes) != 1:
                        print("More or less than one size unit found", size)
                        continue
                    size = sizes[0]
            if not size_seen:
                # products_with_sizes += 1
                print("No size for " + name)
            total_products += 1
        except KeyError as e:
            print("Key Error:", e)
            continue
        if size is None:
            print('size is none')
            continue
        product_sizes.append((name, size))
    if total_products != 0:
        print('proportion: ' + str(products_with_sizes / total_products))
    return product_sizes


if __name__=="__main__":
    try:
        table = boto3.resource('dynamodb').Table('product-data')
        #existing_record = table.query(KeyConditionExpression=Key('query').eq(query))
    except Exception as e:
        print(e)
        sys.exit(-1)
    main(table)
'''
