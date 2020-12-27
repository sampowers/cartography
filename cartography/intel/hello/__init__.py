from cartography.intel.hello import greetings
from cartography.util import timeit


@timeit
def start_hello_ingestion(neo4j_session, config):
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }
    greetings.sync(neo4j_session, common_job_parameters)
