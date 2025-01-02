import time

from kaia.kaia.audio_control.wav_streaming import WavStreamingTestApi, WavApiSettings, WavServerSettings
from demos.kaia.audio_control import create_release_control_settings
from kaia.infra.app import KaiaApp
from kaia.kaia.audio_control.audio_control_cycle import AudioControlCycle
from kaia.kaia.server_2.api import KaiaApi, KaiaServerSettings, Message
from kaia.kaia.server_2.test.test_2_bridge import AudioCycleToKaiaServerBridge, AudioControlBridge
from kaia.infra import Loc

SILENCE_LEVEL = 50

if __name__ == '__main__':
    with Loc.create_temp_folder('kaia_server_test_2_file_cache') as cache:
        with Loc.create_temp_file('kaia_server_test_2', 'db') as db_path:
            kaia_settings = KaiaServerSettings(db_path, cache)
            with KaiaApi.Test(kaia_settings) as kaia_api:
                with WavStreamingTestApi(WavApiSettings(), WavServerSettings(cache)) as streaming_api:
                    audio_settings = create_release_control_settings(streaming_api.settings.address)
                    audio_settings.silence_level=SILENCE_LEVEL
                    audio_settings.api_call_on_produced_file = AudioCycleToKaiaServerBridge(f'127.0.0.1:{kaia_settings.port}', kaia_api.session_id)
                    control_bridge = AudioControlBridge(audio_settings)
                    app = KaiaApp()
                    app.add_subproc_service(control_bridge)
                    with app:
                        while True:
                            updates = kaia_api.pull_updates()
                            for update in updates:
                                if update.type == 'command_audio':
                                    kaia_api.add_message(Message(Message.Type.ToUser, 'Message received'))
                                    kaia_api.add_sound(update.payload['filename'])
                                    break
                            time.sleep(1)





