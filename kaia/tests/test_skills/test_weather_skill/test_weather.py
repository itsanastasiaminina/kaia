from unittest import TestCase
from datetime import datetime
from eaglesong.core import Automaton, Scenario, Return
from kaia.skills.weather.skill import WeatherSkill, WeatherIntents, WeatherReply, WeatherSettings
from kaia.skills.weather.request import get_sample


def S(hour=21):
    return Scenario(automaton_factory=lambda: Automaton(WeatherSkill(
        WeatherSettings(0,0,'Europe/Berlin'),
        lambda: datetime(2023,12,21,hour,15),
        get_sample
    ).run, None))



class WeatherTestCase(TestCase):
    def test_weather(self):
        (
            S()
            .send(WeatherIntents.question.utter())
            .check(
                WeatherReply.weather.utter(
                    temperature_2m = 4.6,
                    weathercode = 80
                ),
                Return
            )
            .validate()
        )



    def test_forecast_today(self):
        (
            S(14)
            .send(WeatherIntents.forecast.utter())
            .check(WeatherReply.forecast.utter(
                for_today=True,
                min_t = 6,
                max_t = 8,
                is_sunny = False,
                precipitations = ('slight rain at 14', 'moderate rain at 15', 'slight rain at 16')
            ), Return)
            .validate()
        )

    def test_forecast_tomorrow(self):
        (
            S(20)
            .send(WeatherIntents.forecast.utter())
            .check(WeatherReply.forecast.utter(
                for_today=False,
                min_t = 2,
                max_t = 3,
                is_sunny = True,
                precipitations = None
            ), Return)
            .validate()
        )
