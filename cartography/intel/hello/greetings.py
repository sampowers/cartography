import logging

from cartography.intel.hello.util import fetch_greetings_gist
from cartography.util import run_cleanup_job
from cartography.util import timeit


logger = logging.getLogger(__name__)


@timeit
def get_greetings():
    return fetch_greetings_gist()


@timeit
def load_greetings(data, neo4j_session, update_tag):
    process_greetznfo = """
    UNWIND {JsonData} as greetznfo
    MERGE (g:Greeting{id: greetznfo.greeting})
    ON CREATE SET g.firstseen = timestamp()
    SET g.place = greetznfo.name,
        g.name = greetznfo.greeting,
        g.visual = greetznfo.visual,
        g.lastupdated = {UpdateTag}
    
    WITH g
    WHERE g.place IS NOT NULL
    MERGE (p:Place{id: g.place})
    ON CREATE SET p.firstseen = timestamp()
    SET p.name = g.place,
    p.lastupdated = {UpdateTag}
        
    MERGE (p)-[r:SAY]->(g)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = r.UpdateTag      
    """
    neo4j_session.run(process_greetznfo, JsonData=data, UpdateTag=update_tag)


@timeit
def cleanup(neo4j_session, common_job_parameters):
    run_cleanup_job('hello_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync_greetings(neo4j_session, update_tag):
    salutations = get_greetings()
    load_greetings(salutations, neo4j_session, update_tag)


@timeit
def sync(neo4j_session, common_job_parameters):
    sync_greetings(neo4j_session, common_job_parameters['UPDATE_TAG'])
