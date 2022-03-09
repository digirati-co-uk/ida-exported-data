from pyelucidate.pyelucidate import async_items_by_container, format_results, mirador_oa
import json


def oa_from_id(identifier, elucidate="https://elucidate.dlcs-ida.org/", request_uri="foo"):
    annotations = async_items_by_container(
        elucidate=elucidate,
        container=identifier,
        header_dict={
            "Accept": "Application/ld+json; profile="
                      + '"http://www.w3.org/ns/anno.jsonld"'
        },
        flatten_ids=True,
        trans_function=mirador_oa,
    )
    content = format_results(list(annotations), request_uri=request_uri)
    return content

