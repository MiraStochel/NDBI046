#!/usr/bin/env python3
import pandas as pd

from rdflib import Graph, BNode, Literal, Namespace
# See https://rdflib.readthedocs.io/en/latest/_modules/rdflib/namespace.html
from rdflib.namespace import QB, RDF, XSD, DCTERMS

NS = Namespace("https://stochel.cz/ontology#")
NSR = Namespace("https://stochel.cz/resources/")
# We use custom Namespace here as the generated is limited in content
# https://rdflib.readthedocs.io/en/stable/_modules/rdflib/namespace/_RDFS.html
RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")

SDMX_CONCEPT = Namespace("http://purl.org/linked-data/sdmx/2009/concept#")
SDMX_CODE = Namespace("http://purl.org/linked-data/sdmx/2009/code#")
SDMX_DIMENSION = Namespace("http://purl.org/linked-data/sdmx/2009/dimension#")
SDMX_ATTRIBUTE = Namespace("http://purl.org/linked-data/sdmx/2009/attribute#")
SDMX_MEASURE = Namespace("http://purl.org/linked-data/sdmx/2009/measure#")


def main():
    data_as_csv = pd.read_csv("narodni-registr-poskytovatelu-zdravotnich-sluzeb.csv")
    data_cube = as_data_cube(data_as_csv)
    print(data_cube.serialize(format="ttl"))
    print("-" * 80)


def as_data_cube(data):
    result = Graph()
    dimensions = create_dimensions(result)
    measures = create_measure(result)
    structure = create_structure(result, dimensions, measures)
    dataset = create_dataset(result, structure)
    create_observations(result, dataset, data)
    return result


def create_dimensions(collector: Graph):

    county = NS.county
    collector.add((county, RDF.type, RDFS.Property))
    collector.add((county, RDF.type, QB.DimensionProperty))
    collector.add((county, RDFS.label, Literal("Okres", lang="cs")))
    collector.add((county, RDFS.label, Literal("County", lang="en")))
    collector.add((county, RDFS.range, XSD.string))
    collector.add((region, QB.concept, SDMX_CONCEPT.classSystem))

    region = NS.region
    collector.add((region, RDF.type, RDFS.Property))
    collector.add((region, RDF.type, QB.DimensionProperty))
    collector.add((region, RDFS.label, Literal("Kraj", lang="cs")))
    collector.add((region, RDFS.label, Literal("Region", lang="en")))
    collector.add((region, RDFS.range, XSD.string))
    collector.add((region, QB.concept, SDMX_CONCEPT.refArea))

    field_of_care = NS.field_of_care
    collector.add((field_of_care, RDF.type, RDFS.Property))
    collector.add((field_of_care, RDF.type, QB.DimensionProperty))
    collector.add((field_of_care, RDFS.label, Literal("Obor péče", lang="cs")))
    collector.add((field_of_care, RDFS.label, Literal("Field of care", lang="en")))
    collector.add((field_of_care, RDFS.range, XSD.string))
    collector.add((region, QB.concept, SDMX_CONCEPT.refArea))

    return [county, region, field_of_care]


def create_measure(collector: Graph):

    number_of_care_providers = NS.number_of_care_providers
    collector.add( ( number_of_care_providers, RDF.type, RDFS.Property) )
    collector.add( ( number_of_care_providers, RDF.type, QB.MeasureProperty ) )
    collector.add( ( number_of_care_providers, RDFS.label, Literal("Počet poskytovatelů péče", lang="cs") ) )
    collector.add( ( number_of_care_providers, RDFS.label, Literal("Number of care providers", lang="en") ) )
    collector.add( ( number_of_care_providers, RDFS.range, XSD.integer ) )
    collector.add( ( number_of_care_providers, RDFS.subPropertyOf, SDMX_MEASURE.obsValue) )

    return [number_of_care_providers]


def create_structure(collector: Graph, dimensions, measures):

    structure = NS.structure
    collector.add( ( structure, RDF.type, QB.DataStructureDefinition ) )

    for dimension in dimensions:
        component = BNode()
        collector.add((structure, QB.component, component))
        collector.add((component, QB.dimension, dimension))

    for measure in measures:
        component = BNode()
        collector.add((structure, QB.component, component))
        collector.add((component, QB.measure, measure))

    return structure


def create_dataset(collector: Graph, structure):

    dataset = NSR.dataCubeInstance
    collector.add((dataset, RDF.type, QB.DataSet))
    collector.add((dataset, RDFS.label, Literal(
        "Number of care providers", lang="en")))
    collector.add((dataset, QB.structure, structure))
    collector.add((dataset, DCTERMS.issued, Literal("2023-03-13", datatype=XSD.date)))
    collector.add((dataset, DCTERMS.modified, Literal("2023-03-13", datatype=XSD.date)))
    collector.add((dataset, DCTERMS.publisher, Literal("https://stochel.cz", datatype=XSD.anyURI)))
    collector.add((dataset, DCTERMS.license, Literal("https://creativecommons.org/licenses/by/4.0/", datatype=XSD.anyURI)))
    collector.add((dataset, DCTERMS.title, Literal("Care providers", lang="en")))
    collector.add((dataset, DCTERMS.subject, Literal("Number of care providers in areas", lang="en")))
    collector.add((dataset, DCTERMS.description, Literal("Number of care providers in areas in Czech Republic", lang="en")))
    collector.add((dataset, RDFS.comment, Literal("Number of care providers in areas in Czech Republic", lang="en")))

    return dataset


def create_observations(collector: Graph, dataset, data):
    data_grouped = data.groupby(["Okres", "Kraj", "OborPece"])
    sizes = data_grouped.size().array ## Velmi krkolomne, ale co uz
    for index, row in enumerate(data_grouped):
        resource = NSR["observation-" + str(index).zfill(8)]
        create_observation(collector, dataset, resource, row, sizes[index])


def create_observation(collector: Graph, dataset, resource, data, number):
    collector.add((resource, RDF.type, QB.Observation))
    collector.add((resource, QB.dataSet, dataset))
    collector.add((resource, NS.county, Literal(data[0][0])))
    collector.add((resource, NS.region, Literal(data[0][1])))
    collector.add((resource, NS.field_of_care, Literal(data[0][2])))
    collector.add((resource, NS.number_of_care_providers, Literal(
        number, datatype=XSD.integer)))

def convert_date(value):
    return value.replace(".", "-")

if __name__ == "__main__":
    main()
