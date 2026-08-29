"""Astronomical calculations for the Clemson observing location.

Uses Skyfield and the JPL DE421 ephemeris to calculate:
- Current positions of planets, stars, the Sun, and Moon
- Altitude and azimuth
- Basic nighttime visibility
- Sunset, sunrise, and darkness timing
- Moon phase and illumination
- Tonight's highlights
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
import math

from skyfield import almanac
from skyfield.api import Loader, Star, wgs84

from .schemas import Location, SkyObject


PLANET_INFO = {
    "Mercury": (
        -0.4,
        "Mercury has extreme temperature changes.",
    ),
    "Venus": (
        -4.0,
        "Venus is hotter than Mercury because of its thick atmosphere.",
    ),
    "Mars": (
        1.0,
        "Mars appears reddish because iron minerals oxidize in its soil.",
    ),
    "Jupiter": (
        -2.0,
        "Jupiter is the largest planet and has four easily observed Galilean moons.",
    ),
    "Saturn": (
        0.7,
        "Saturn's rings are made mostly of ice and rock particles.",
    ),
    "Uranus": (
        5.7,
        "Uranus rotates on its side relative to most planets.",
    ),
    "Neptune": (
        7.8,
        "Neptune was predicted mathematically before it was observed.",
    ),
}


BRIGHT_STARS = {
    "Sirius": (
        6.7525,
        -16.7161,
        -1.46,
        "Sirius is the brightest star in Earth's night sky.",
    ),
    "Vega": (
        18.6156,
        38.7837,
        0.03,
        "Vega is one of the three stars in the Summer Triangle.",
    ),
    "Arcturus": (
        14.261,
        19.182,
        -0.05,
        "Arcturus is an orange giant star relatively close to the Sun.",
    ),
}


PLANET_TARGETS = {
    "Mercury": "mercury",
    "Venus": "venus",
    "Mars": "mars",
    "Jupiter": "jupiter barycenter",
    "Saturn": "saturn barycenter",
    "Uranus": "uranus barycenter",
    "Neptune": "neptune barycenter",
}


def _direction(azimuth: float) -> str:
    """Turn an azimuth into a cardinal/intercardinal direction."""
    directions = [
        "N",
        "NE",
        "E",
        "SE",
        "S",
        "SW",
        "W",
        "NW",
    ]

    return directions[int((azimuth + 22.5) // 45) % 8]


def _local_dt(
    dt: datetime,
    timezone_name: str,
) -> datetime:
    """Convert a UTC-aware datetime into the requested local timezone."""
    return dt.astimezone(
        ZoneInfo(timezone_name)
    )


class AstronomyEngine:
    """Reusable Skyfield engine."""

    def __init__(self, data_dir: str):
        data_path = Path(data_dir)
        data_path.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.loader = Loader(
            str(data_path)
        )

        self.ts = (
            self.loader.timescale()
        )

        self.eph = self.loader(
            "de421.bsp"
        )

    def calculate(
        self,
        location: Location,
        when: datetime | None = None,
    ) -> dict:
        """Calculate the current astronomical state."""

        current = (
            when
            or datetime.now(timezone.utc)
        )

        if current.tzinfo is None:
            current = current.replace(
                tzinfo=timezone.utc
            )

        current = current.astimezone(
            timezone.utc
        )

        t = self.ts.from_datetime(
            current
        )

        # Used for calculating object positions.
        observer = (
            self.eph["earth"]
            + wgs84.latlon(
                location.latitude,
                location.longitude,
            )
        )

        # -----------------------------------
        # Determine current Sun altitude
        # -----------------------------------

        sun_apparent = (
            observer.at(t)
            .observe(self.eph["sun"])
            .apparent()
        )

        sun_altitude = float(
            sun_apparent.altaz()[0].degrees
        )

        dark_enough = (
            sun_altitude < -6
        )

        # -----------------------------------
        # Build object list
        # -----------------------------------

        objects: list[SkyObject] = []

        targets = [
            (
                name,
                self.eph[
                    PLANET_TARGETS[name]
                ],
                "planet",
                magnitude,
                fact,
            )
            for name, (
                magnitude,
                fact,
            ) in PLANET_INFO.items()
        ]

        targets += [
            (
                "Moon",
                self.eph["moon"],
                "moon",
                -12.0,
                (
                    "The Moon's phases are caused "
                    "by the changing angle between "
                    "the Sun, Moon, and Earth."
                ),
            ),
            (
                "Sun",
                self.eph["sun"],
                "sun",
                -26.7,
                (
                    "The Sun is a star, and its "
                    "apparent brightness comes from "
                    "its short distance from Earth."
                ),
            ),
        ]

        targets += [
            (
                name,
                Star(
                    ra_hours=ra,
                    dec_degrees=dec,
                ),
                "star",
                magnitude,
                fact,
            )
            for name, (
                ra,
                dec,
                magnitude,
                fact,
            ) in BRIGHT_STARS.items()
        ]

        for (
            name,
            body,
            object_type,
            magnitude,
            fact,
        ) in targets:

            apparent = (
                observer.at(t)
                .observe(body)
                .apparent()
            )

            altitude, azimuth, _ = (
                apparent.altaz()
            )

            altitude_deg = float(
                altitude.degrees
            )

            azimuth_deg = float(
                azimuth.degrees
            )

            above_horizon = (
                altitude_deg > 0
            )

            visible = (
                altitude_deg > 5
                and (
                    object_type == "sun"
                    or dark_enough
                )
            )

            # The Moon can be useful during
            # twilight if it is above the horizon.
            if (
                object_type == "moon"
                and altitude_deg > 5
                and sun_altitude < 0
            ):
                visible = True

            if object_type == "sun":
                best_for = "daylight only"

            elif name == "Jupiter":
                best_for = (
                    "naked eye; binoculars for moons"
                )

            elif name == "Saturn":
                best_for = (
                    "naked eye; telescope for rings"
                )

            elif (
                magnitude is not None
                and magnitude < 4.5
            ):
                best_for = "naked eye"

            else:
                best_for = "telescope"

            objects.append(
                SkyObject(
                    name=name,
                    object_type=object_type,
                    above_horizon=above_horizon,
                    visible=visible,
                    altitude_deg=round(
                        altitude_deg,
                        2,
                    ),
                    azimuth_deg=round(
                        azimuth_deg,
                        2,
                    ),
                    magnitude=magnitude,
                    direction=_direction(
                        azimuth_deg
                    ),
                    best_for=best_for,
                    educational_fact=fact,
                )
            )

        # -----------------------------------
        # Sun / twilight events
        # -----------------------------------

        (
            sunset,
            sunrise_next,
            darkness_start,
        ) = self._solar_events(
            location,
            current,
        )

        # -----------------------------------
        # Moon
        # -----------------------------------

        illumination = (
            self._moon_illumination(t)
        )

        # -----------------------------------
        # Highlights
        # -----------------------------------

        highlights = self._highlights(
            objects
        )

        return {
            "observed_at": _local_dt(
                current,
                location.timezone,
            ),
            "sunset": sunset,
            "sunrise_next": sunrise_next,
            "darkness_start": darkness_start,
            "moon_phase": self._moon_phase(
                illumination
            ),
            "moon_illumination_percent": round(
                illumination * 100,
                1,
            ),
            "objects": sorted(
                objects,
                key=lambda obj: (
                    -obj.visible,
                    -obj.altitude_deg,
                ),
            ),
            "highlights": highlights,
        }

    def object_altitude(
        self,
        location: Location,
        object_name: str,
        when: datetime,
    ) -> float:
        """Return an object's altitude at a specific time."""

        calculated = self.calculate(
            location,
            when,
        )

        for obj in calculated["objects"]:
            if (
                obj.name.lower()
                == object_name.lower()
            ):
                return obj.altitude_deg

        raise ValueError(
            f"Unknown astronomy object: {object_name}"
        )

    def _solar_events(
        self,
        location: Location,
        current_utc: datetime,
    ) -> tuple[
        datetime,
        datetime,
        datetime,
    ]:
        """Calculate upcoming sunset, sunrise, and darkness."""

        local_now = _local_dt(
            current_utc,
            location.timezone,
        )

        local_date = local_now.date()

        local_midnight = datetime.combine(
            local_date,
            datetime.min.time(),
            tzinfo=ZoneInfo(
                location.timezone
            ),
        )

        # Search a 2-day window so we have
        # enough time to find upcoming events.
        search_start = (
            local_midnight
            - timedelta(days=1)
        )

        search_end = (
            local_midnight
            + timedelta(days=2)
        )

        start_t = self.ts.from_datetime(
            search_start.astimezone(
                timezone.utc
            )
        )

        end_t = self.ts.from_datetime(
            search_end.astimezone(
                timezone.utc
            )
        )

        # IMPORTANT:
        # dark_twilight_day() expects the geographic
        # location itself, NOT Earth + location.
        topos = wgs84.latlon(
            location.latitude,
            location.longitude,
        )

        times, phases = (
            almanac.find_discrete(
                start_t,
                end_t,
                almanac.dark_twilight_day(
                    self.eph,
                    topos,
                ),
            )
        )

        events = []

        for sky_time, phase in zip(
            times,
            phases,
        ):
            event = _local_dt(
                sky_time.utc_datetime(),
                location.timezone,
            )

            events.append(
                (
                    event,
                    int(phase),
                )
            )

        # Fallback values. These are only used
        # if Skyfield does not return an event.
        sunset = (
            local_midnight
            + timedelta(hours=18)
        )

        sunrise_next = (
            local_midnight
            + timedelta(days=1, hours=6)
        )

        darkness_start = (
            local_midnight
            + timedelta(hours=20)
        )

        # Skyfield states:
        #
        # 0 = astronomical darkness
        # 1 = astronomical twilight
        # 2 = nautical twilight
        # 3 = civil twilight
        # 4 = daylight
        #
        # Sunset = transition into civil twilight.
        # Sunrise = transition into daylight.
        # Darkness start = transition into astronomical darkness.

        future_events = [
            (
                event,
                phase,
            )
            for event, phase in events
            if event > local_now
        ]

        sunset_candidates = [
            event
            for event, phase in future_events
            if phase == 3
        ]

        sunrise_candidates = [
            event
            for event, phase in future_events
            if phase == 4
        ]

        darkness_candidates = [
            event
            for event, phase in future_events
            if phase == 0
        ]

        if sunset_candidates:
            sunset = sunset_candidates[0]

        if sunrise_candidates:
            sunrise_next = sunrise_candidates[0]

        if darkness_candidates:
            darkness_start = darkness_candidates[0]

        return (
            sunset,
            sunrise_next,
            darkness_start,
        )

    @staticmethod
    def _highlights(
        objects: list[SkyObject],
    ) -> list[SkyObject]:
        """Choose up to three good observing targets."""

        candidates = [
            obj
            for obj in objects
            if (
                obj.visible
                and obj.object_type != "sun"
                and obj.altitude_deg >= 15
            )
        ]

        candidates.sort(
            key=lambda obj: (
                obj.magnitude
                if obj.magnitude is not None
                else 99,
                -obj.altitude_deg,
            )
        )

        return candidates[:3]

    def _moon_illumination(
        self,
        t,
    ) -> float:
        """Estimate Moon illumination from Sun-Moon elongation."""

        earth = self.eph["earth"]

        sun = (
            earth.at(t)
            .observe(self.eph["sun"])
            .apparent()
        )

        moon = (
            earth.at(t)
            .observe(self.eph["moon"])
            .apparent()
        )

        elongation = (
            sun.separation_from(moon).degrees
        )

        return (
            1
            - math.cos(
                math.radians(
                    elongation
                )
            )
        ) / 2

    @staticmethod
    def _moon_phase(
        illumination: float,
    ) -> str:
        """Return a simple educational Moon phase label."""

        if illumination < 0.03:
            return "New moon"

        if illumination < 0.48:
            return "Crescent moon"

        if illumination < 0.52:
            return "Quarter moon"

        if illumination < 0.97:
            return "Gibbous moon"

        return "Full moon"