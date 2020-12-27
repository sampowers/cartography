
import cartography.intel.hello.greetings
import tests.data.hello.greetings

TEST_UPDATE_TAG = 123456789


def test_load_greeting_data(neo4j_session):
    cartography.intel.hello.greetings.load_greetings(
        tests.data.hello.greetings.GREETINGS,
        neo4j_session,
        TEST_UPDATE_TAG
    )

    greeting_nodes = neo4j_session.run(
        """
        MATCH (n:Greeting) RETURN n.id;
        """,
    )
    greeting_actual_nodes = {n['n.id'] for n in greeting_nodes}
    greeting_expected_nodes = {
        "Hola",
        "Marhaba",
        "Senga yai",
    }

    assert greeting_actual_nodes == greeting_expected_nodes

    place_nodes = neo4j_session.run(
        """
        MATCH (n:Place) RETURN n.name;
        """,
    )
    place_expected_nodes = {
        "Andorra",
        "United Arab Emirates",
        "Afghanistan",
    }
    place_actual_nodes = {n['n.name'] for n in place_nodes}

    assert place_actual_nodes == place_expected_nodes

