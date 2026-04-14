#!/usr/bin/env python3


"""Issues types reported to the radkummerkasten map."""

import enum

__all__ = ["IssueType"]


class IssueType(enum.Enum):
    """The types of issue that can be reported."""
    # pylint: disable=too-few-public-methods

    # Status Quo:

    # a) Frontend:
    # Gefahrenstelle
    # Lückenschluss
    # Einbahn öffnen
    # Radbügel
    # Markierung oder Schild
    # Ampel
    # Hindernis
    # Anderes

    # b) Datenbank
    # Ampelschaltung    1537
    # Anderes           1249
    # Beschilderung        1
    # Bodenmarkierung    907
    # Einbahn öffnen    1351
    # Gefahrenstelle    2899
    # Hindernisse        747
    # Lückenschluss     1293
    # Radabstellanlage  1968

    GEFAHRENSTELLE = "Gefahrenstelle"
    LUECKENSCHLUSS = "Lückenschluss"
    EINBAHN_OEFFNEN = "Einbahn öffnen"
    RADBUEGEL = "Radbügel"
    MARKIERUNG_ODER_SCHILD = "Markierung oder Schild"
    AMPEL = "Ampel"
    HINDERNIS = "Hindernis"
    ANDERES = "Anderes"

    # TODO: make this configurable/dynamic?
