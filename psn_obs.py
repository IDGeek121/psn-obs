import psn
import obspython as obs
import threading
import datetime


def get_datetime_fromisoformat(str_in: str) -> datetime.datetime:
    year = int(str_in[0:4])
    month = int(str_in[5:7])
    day = int(str_in[8:10])
    hour = int(str_in[11:13])
    minute = int(str_in[14:16])
    sec = int(str_in[17:19])
    retval = datetime.datetime(year, month, day, hour, minute, sec, 0, None)
    return retval

# Daemon thread that will query the server for the earned trophies every 5 seconds.
def update_trophy_earned_status():
    global state

    # New query every 'timeout' seconds
    while not state.exit.wait(timeout = 4.0):
        #print('update_trophy_earned_status')
        if state.trophy_title:
            state.earned_trophies = psn.get_trophies_earned_for_title(state.token, state.trophy_title)

            # Let's examine the lastUpdatedDateTime and see if we earned any
            # trophies since the last query. If so, we need to generate a list
            # of trophies to print out, which will involve iterating over every
            # trophy and checking its progressedDateTime or earnedDateTime.
            new_earned_datetime = get_datetime_fromisoformat(state.earned_trophies['lastUpdatedDateTime'][:-1])
            # Ignore if first query
            if not state.previous_earned_datetime:
                state.previous_earned_datetime = new_earned_datetime
            if state.previous_earned_datetime < new_earned_datetime:
                # List generation
                for trophy in state.earned_trophies['trophies']:
                    if 'progressedDateTime' in trophy:
                        progressed_datetime = get_datetime_fromisoformat(trophy['progressedDateTime'][:-1])
                        if state.previous_earned_datetime < progressed_datetime:
                            state.list_of_trophies_to_display.append(trophy['trophyId'])
                    elif trophy['earned']:
                        earned_datetime = get_datetime_fromisoformat(trophy['earnedDateTime'][:-1])
                        if state.previous_earned_datetime < earned_datetime:
                            state.list_of_trophies_to_display.append(trophy['trophyId'])

                # Epilog. Update the time and kick off the display state.
                state.previous_earned_datetime = new_earned_datetime
                state.trophy_display_state = 4
        else:
            print('trophy title not found')
    print('end of "update_trophy_earned_status" thread')

# Used as a struct for program data. Holds the current return values from
# queries to the PSN Trophies API.
class PSNState:
    npsso = ''
    token = ''
    previous_earned_datetime = None #datetime.datetime(2000, 1, 1, 0, 0, 0, 0, None)
    list_of_trophies_to_display = []
    trophy_titles = {}
    trophy_title = {}
    trophies = {}
    trophy = {}
    earned_trophies = {}
    earned_trophy = {}
    trophy_display_state = 0
    trophy_display_opacity = 0.
    trophy_display_dt = 0
    exit = threading.Event()
    psn_thread = threading.Thread(target = update_trophy_earned_status, daemon = True)

state = PSNState()

def script_unload():
    print('script_unload')
    global state
    state.exit.set()
    state.psn_thread.join()

def script_load(settings):
    obs.obs_data_erase(settings, 'game_list')
    obs.obs_data_erase(settings, 'trophy_list')

def script_tick(seconds):
    global state
    # States that actually do something
    if state.trophy_display_state != 0:
        state.trophy_display_dt += seconds
        # Display on screen for a few seconds
        if state.trophy_display_state == 2:
            if state.trophy_display_dt >= 4.:
                state.trophy_display_dt = 0.
                state.trophy_display_state = 3
        # Get next trophy in the list and set the image/description
        elif state.trophy_display_state == 4:
            if state.list_of_trophies_to_display:
                index = state.list_of_trophies_to_display.pop(0)
                state.trophy = state.trophies['trophies'][index]
                state.earned_trophy = state.earned_trophies['trophies'][index]
                display_trophy_progress()
                state.trophy_display_state = 1
        # States that involve fades in (1) and out (3)
        else:
            group_source = obs.obs_get_source_by_name('trophy_group')
            group_source_opacity_filter = obs.obs_source_get_filter_by_name(group_source, 'opacity')
            group_source_opacity_filter_settings = obs.obs_source_get_settings(group_source_opacity_filter)
            if state.trophy_display_state == 1:
                state.trophy_display_opacity = min(state.trophy_display_opacity + (1. - state.trophy_display_opacity) * (state.trophy_display_dt * 6.), 1.)
                if state.trophy_display_opacity == 1.:
                    state.trophy_display_dt = 0.
                    state.trophy_display_state = 2
            elif state.trophy_display_state == 3:
                state.trophy_display_opacity = max(state.trophy_display_opacity + (0. - state.trophy_display_opacity) * (state.trophy_display_dt * 6.), 0.)
                if state.trophy_display_opacity == 0.:
                    state.trophy_display_dt = 0.
                    state.trophy_display_state = 4
            obs.obs_data_set_double(group_source_opacity_filter_settings, 'opacity', state.trophy_display_opacity)
            obs.obs_source_update(group_source_opacity_filter, group_source_opacity_filter_settings)
            obs.obs_source_release(group_source_opacity_filter)
            obs.obs_source_release(group_source)
    # Don't do anything
    else:
        state.trophy_display_dt = 0.
        

def script_description():
    return '''<h1>PSN Trophies</h1>
Track trophies for a PSN account.'''


def script_defaults(settings):
    global state
    print(f'{obs.obs_data_get_json(settings)}')
    state.psn_thread.start()

def script_properties():
    print('script_properties')
    props = obs.obs_properties_create()

    npsso_text = obs.obs_properties_add_text(props, 'npsso', 'npsso', obs.OBS_TEXT_PASSWORD)

    obs.obs_properties_add_button(props, 'get_token', 'Get Token', get_token)

    game_list = obs.obs_properties_add_list(props,
                                            'game_list',
                                            'Games',
                                            obs.OBS_COMBO_TYPE_LIST,
                                            obs.OBS_COMBO_FORMAT_STRING)

    obs.obs_property_set_modified_callback(game_list, game_list_callback)

    obs.obs_properties_add_button(props, 'get_trophy_titles', 'Get Game List',
                                  lambda props, prop: True if populate_list_property_with_trophy_titles(
                                      game_list) else True)

    # trophy_list = obs.obs_properties_add_list(props,
    #                                           'trophy_list',
    #                                           'Trophies',
    #                                           obs.OBS_COMBO_TYPE_LIST,
    #                                           obs.OBS_COMBO_FORMAT_INT)

    # obs.obs_property_set_modified_callback(trophy_list, trophy_list_callback)

    # obs.obs_properties_add_button(props, 'get_trophies', 'Get Trophies',
    #                               lambda props, prop: True if populate_list_property_with_trophies_for_title(
    #                                   trophy_list) else True)

    obs.obs_properties_add_button(props, 'test_notif', 'Test Notification', test_notif)

    return props

def test_notif(props, property):
    global state
    state.trophy_display_state = 1


def script_update(settings):
    print('script_update')
    global state
    state.npsso = obs.obs_data_get_string(settings, 'npsso')


def get_token(props, property):
    print('get_token')
    global state
    state.token = psn.get_psn_token(state.npsso)
    return True


def populate_list_property_with_trophy_titles(list_property):
    global state
    state.trophy_titles = psn.get_trophy_titles(state.token)
    obs.obs_property_list_clear(list_property)
    obs.obs_property_list_add_string(list_property, '', '')
    for trophy_title in state.trophy_titles['trophyTitles']:
        trophy_title_name = f'{trophy_title["trophyTitleName"]} ({trophy_title["trophyTitlePlatform"]})'
        trophy_title_npCommunicationId = trophy_title["npCommunicationId"]
        obs.obs_property_list_add_string(list_property,
                                         trophy_title_name,
                                         trophy_title_npCommunicationId)
    return True


def populate_list_property_with_trophies_for_title(list_property):
    global state
    obs.obs_property_list_clear(list_property)
    obs.obs_property_list_add_string(list_property, '', '')
    state.trophies = psn.get_trophies_for_title(state.token, state.trophy_title)
    state.earned_trophies = psn.get_trophies_earned_for_title(state.token, state.trophy_title)

    for trophy in state.trophies['trophies']:
        trophy_earned = state.earned_trophies['trophies'][trophy['trophyId']]['earned']
        if not trophy_earned:
            trophy_name = trophy['trophyName']
            trophy_desc = trophy['trophyDetail']
            obs.obs_property_list_add_int(list_property,
                                             f'{trophy_name}: {trophy_desc}',
                                             trophy['trophyId'])

    return True


def game_list_callback(props, prop, settings):
    print('game_list_callback')
    # On refresh, set the trophyTitle correctly.
    global state
    refresh = False
    
    if state.trophy_titles:
        # Search the trophyTitles list for the trophyTitle dict that we want.
        npCommunicationId = obs.obs_data_get_string(settings, 'game_list')
        for temp_trophy_title in state.trophy_titles['trophyTitles']:
            if npCommunicationId == temp_trophy_title['npCommunicationId']:
                state.trophy_title = temp_trophy_title
                state.trophies = psn.get_trophies_for_title(state.token, state.trophy_title)

    return refresh


def trophy_list_callback(props, prop, settings):
    global state
    print('trophy_list_callback')
    if state.trophies:
        state.trophy_id = obs.obs_data_get_int(settings, 'trophy_list')
        for temp_trophy in state.trophies['trophies']:
            if state.trophy_id == temp_trophy['trophyId']:
                state.trophy = temp_trophy
        

def display_trophy_progress():
    print('display_trophy_progress')
    global state

    # Set text to trophy description
    text_source = obs.obs_get_source_by_name('trophy_text')
    text_source_settings = obs.obs_source_get_settings(text_source)
    progress_string = ''
    if 'progressRate' in state.earned_trophy:
        progress_string = f'\n{state.earned_trophy["progressRate"]}% ({state.earned_trophy["progress"]})'
    obs.obs_data_set_string(text_source_settings, 'text', f'{state.trophy["trophyName"]}\n{state.trophy["trophyDetail"]}{progress_string}')
    obs.obs_source_update(text_source, text_source_settings)
    obs.obs_source_release(text_source)

    # Set image to trophy image
    browser_source = obs.obs_get_source_by_name('trophy_image')
    browser_source_settings = obs.obs_source_get_settings(browser_source)
    obs.obs_data_set_string(browser_source_settings, 'url', state.trophy['trophyIconUrl'])
    obs.obs_source_update(browser_source, browser_source_settings)
    obs.obs_source_release(browser_source)
