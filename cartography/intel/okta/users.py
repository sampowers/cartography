# Okta intel module - Users
import logging

from okta import UsersClient

from cartography.intel.okta import get_okta_api_key


logger = logging.getLogger(__name__)


def _create_user_client(okta_org):
    """
    Create Okta User Client
    :param okta_org: Okta organization name
    :return: Instance of UsersClient
    """
    # https://github.com/okta/okta-sdk-python/blob/master/okta/models/user/User.py
    user_client = UsersClient(
        base_url=f"https://{okta_org}.okta.com/",
        api_token=get_okta_api_key(),
    )

    return user_client


def _get_okta_users(user_client):
    """
    Get Okta users from Okta server
    :param user_client: user client
    :return: Array of dictionary containing user properties
    """
    user_list = []
    paged_users = user_client.get_paged_users()
    while True:
        for current_user in paged_users.result:
            user_props = transform_okta_user(current_user)
            user_list.append(user_props)
        if not paged_users.is_last_page():
            # Keep on fetching pages of users until the last page
            paged_users = user_client.get_paged_users(url=paged_users.next_url)
        else:
            break

    return user_list


def transform_okta_user(okta_user):
    """
    Transform okta user data
    :param okta_user: okta user object
    :return: Dictionary container user properties for ingestion
    """

    # https://github.com/okta/okta-sdk-python/blob/master/okta/models/user/User.py
    user_props = {}
    user_props["first_name"] = okta_user.profile.firstName
    user_props["last_name"] = okta_user.profile.lastName
    user_props["login"] = okta_user.profile.login
    user_props["email"] = okta_user.profile.email
    user_props["second_email"] = okta_user.profile.secondEmail
    user_props["mobile_phone"] = okta_user.profile.mobilePhone

    # https://github.com/okta/okta-sdk-python/blob/master/okta/models/user/User.py
    user_props["id"] = okta_user.id
    user_props["created"] = okta_user.created.strftime("%m/%d/%Y, %H:%M:%S")
    if okta_user.activated:
        user_props["activated"] = okta_user.activated.strftime("%m/%d/%Y, %H:%M:%S")
    else:
        user_props["activated"] = None

    if okta_user.statusChanged:
        user_props["status_changed"] = okta_user.statusChanged.strftime("%m/%d/%Y, %H:%M:%S")
    else:
        user_props["status_changed"] = None

    if okta_user.lastLogin:
        user_props["last_login"] = okta_user.lastLogin.strftime("%m/%d/%Y, %H:%M:%S")
    else:
        user_props["last_login"] = None

    if okta_user.lastUpdated:
        user_props["okta_last_updated"] = okta_user.lastUpdated.strftime("%m/%d/%Y, %H:%M:%S")
    else:
        user_props["okta_last_updated"] = None

    if okta_user.passwordChanged:
        user_props["password_changed"] = okta_user.passwordChanged.strftime("%m/%d/%Y, %H:%M:%S")
    else:
        user_props["password_changed"] = None

    if okta_user.transitioningToStatus:
        user_props["transition_to_status"] = okta_user.transitioningToStatus
    else:
        user_props["transition_to_status"] = None

    return user_props


def _load_okta_users(neo4j_session, okta_org_id, user_list, okta_update_tag):
    """
    Load Okta user information into the graph
    :param neo4j_session: session with neo4j server
    :param okta_org_id: oktat organization id
    :param user_list: list of users
    :param okta_update_tag: The timestamp value to set our new Neo4j resources with
    :return: Nothing
    """

    ingest_statement = """
    MATCH (org:OktaOrganization{id: {ORG_ID}})
    WITH org
    UNWIND {USER_LIST} as user_data
    MERGE (new_user:OktaUser{id: user_data.id})
    ON CREATE SET new_user.firstseen = timestamp()
    SET new_user.first_name = user_data.first_name,
    new_user.last_name = user_data.last_name,
    new_user.login = user_data.login,
    new_user.email = user_data.email,
    new_user.second_email = user_data.second_email,
    new_user.mobile_phone = user_data.mobile_phone,
    new_user.created = user_data.created,
    new_user.activated = user_data.activated,
    new_user.status_changed = user_data.status_changed,
    new_user.last_login = user_data.last_login,
    new_user.okta_last_updated = user_data.okta_last_updated,
    new_user.password_changed = user_data.password_changed,
    new_user.transition_to_status = user_data.transition_to_status,
    new_user.lastupdated = {okta_update_tag}
    WITH new_user, org
    MERGE (org)-[org_r:RESOURCE]->(new_user)
    ON CREATE SET org_r.firstseen = timestamp()
    SET org_r.lastupdated = {okta_update_tag}
    WITH new_user
    MERGE (h:Human{email: new_user.email})
    ON CREATE SET new_user.firstseen = timestamp()
    SET h.lastupdated = {okta_update_tag}
    MERGE (h)-[r:IDENTITY_OKTA]->(new_user)
    ON CREATE SET new_user.firstseen = timestamp()
    SET h.lastupdated = {okta_update_tag}
    """

    neo4j_session.run(
        ingest_statement,
        ORG_ID=okta_org_id,
        USER_LIST=user_list,
        okta_update_tag=okta_update_tag,
    )


def sync_okta_users(neo4j_session, okta_org_id, okta_update_tag, okta_api_key):
    """
    Sync okta users
    :param neo4j_session: Session with Neo4j server
    :param okta_org_id: Okta organization id to sync
    :param okta_update_tag: The timestamp value to set our new Neo4j resources with
    :param okta_api_key: Okta API key
    :return: Nothing
    """

    logger.debug("Syncing Okta users")
    user_client = _create_user_client(okta_org_id, okta_api_key)
    data = _get_okta_users(user_client)

    _load_okta_users(neo4j_session, okta_org_id, data, okta_update_tag)
