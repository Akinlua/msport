https://apigw.bet9ja.com/sportsbook/search/SearchV2?source=desktop&v_cache_version=1.274.3.186

form-data: TERM:CA Bizertin CA Bizertin
START:0
ROWS:100000
ISCOMPETITION:0
ISEVENT:1
ISTEAM:0
GROUPBYFIELD:sp_id
GROUPBYLIMIT:11

{
    "R": "OK",
    "D": {
        "numFound": 1,
        "start": 0,
        "S": {
            "1": {
                "S_ID": "1",
                "S_DESC": "Soccer",
                "S_INCTYPE": "0",
                "S_LANG": "{\"en\":\"Soccer\",\"es\":\"Soccer\"}",
                "P": "10",
                "S_KEY": "S",
                "S_RES_FREQ": "0",
                "E": [
                    {
                        "INCTYPE": 0,
                        "ST": 1,
                        "GID": 967783,
                        "C": "2609",
                        "STARTDATE": "2025-05-11 14:00:00",
                        "SGID": 11420,
                        "EXTID": "60323257",
                        "PLAYER_EID": 0,
                        "DS": "CS Sfaxien - CA Bizertin",
                        "SID": 1,
                        "P": 0,
                        "PRV": 1,
                        "ENDVISIBILITYDATE": "2025-05-11 14:00:00",
                        "ID": 594248600,
                        "PL": 0,
                        "TYPE": 0,
                        "GN": "Ligue 1",
                        "GP": 100,
                        "SG": "Tunisia",
                        "S": "Soccer",
                        "EXCLUDED_BONUS": [],
                        "O": {
                            "S_1X2_1": "1.88",
                            "S_1X2_X": "2.87",
                            "S_1X2_2": "4.6",
                            "S_DC_1X": "1.11",
                            "S_DC_12": "1.3",
                            "S_DC_X2": "1.72",
                            "S_OU@0.5_O": "1.12",
                            "S_OU@0.5_U": "5.3",
                            "S_OU@1.5_O": "1.62",
                            "S_OU@1.5_U": "2.07",
                            "S_OU@2.5_O": "2.95",
                            "S_OU@2.5_U": "1.33",
                            "S_OU@3.5_O": "6.1",
                            "S_OU@3.5_U": "1.07",
                            "S_OU@4.5_O": "12",
                            "S_OU@5.5_O": "21",
                            "S_1X21T_1": "2.67",
                            "S_1X21T_X": "1.76",
                            "S_1X21T_2": "5.3",
                            "S_DC1T_1X": "1.06",
                            "S_DC1T_12": "1.78",
                            "S_DC1T_X2": "1.32",
                            "S_GOALS1T_1": "2.48",
                            "S_GOALS1T_2": "5.4",
                            "S_GOALS1T_3": "14.75",
                            "S_OE_OD": "1.88",
                            "S_OE_EV": "1.76"
                        },
                        "AUX": {
                            "S_OU": [
                                0.5,
                                1.5,
                                2.5,
                                3.5,
                                4.5,
                                5.5
                            ]
                        }
                    }
                ],
                "MK": [
                    {
                        "ID": "S_1X2",
                        "NAME": "1X2",
                        "P": "1",
                        "VW": "0",
                        "CNT": "GR",
                        "CNTLABEL": "Generic Result",
                        "GCAT": "POPULAR",
                        "SV": null,
                        "SGN": [
                            "1",
                            "X",
                            "2"
                        ],
                        "SGNK": [
                            "1",
                            "X",
                            "2"
                        ],
                        "transKeys": {
                            "marketNameKey": "M#S_1X2.NAME",
                            "marketDescKey": "M#S_1X2.DESC",
                            "signs": {
                                "1": "MCU#S_1X2_1",
                                "2": "MCU#S_1X2_2",
                                "X": "MCU#S_1X2_X"
                            }
                        }
                    },
                    {
                        "ID": "S_DC",
                        "NAME": "Double Chance",
                        "P": "2",
                        "VW": "0",
                        "CNT": "GR",
                        "CNTLABEL": "Generic Result",
                        "GCAT": "POPULAR",
                        "SV": null,
                        "SGN": [
                            "1X",
                            "12",
                            "X2"
                        ],
                        "SGNK": [
                            "1X",
                            "12",
                            "X2"
                        ],
                        "transKeys": {
                            "marketNameKey": "M#S_DC.NAME",
                            "marketDescKey": "M#S_DC.DESC",
                            "signs": {
                                "12": "MCU#S_DC_12",
                                "1X": "MCU#S_DC_1X",
                                "X2": "MCU#S_DC_X2"
                            }
                        }
                    },
                    {
                        "ID": "S_OU",
                        "NAME": "Over / Under",
                        "P": "3",
                        "VW": "3",
                        "CNT": "G",
                        "CNTLABEL": "Goals",
                        "GCAT": "POPULAR",
                        "SV": null,
                        "SGN": [
                            "Over ",
                            "Under "
                        ],
                        "SGNK": [
                            "O",
                            "U"
                        ],
                        "AUX": [
                            "1.5",
                            "2.5"
                        ],
                        "transKeys": {
                            "marketNameKey": "M#S_OU.NAME",
                            "marketDescKey": "M#S_OU.DESC",
                            "marketHeaderLabelKey": "MH#S_OU",
                            "signs": {
                                "O": "MCU#S_OU_O",
                                "U": "MCU#S_OU_U"
                            }
                        }
                    },
                    {
                        "ID": "S_1X21T",
                        "NAME": "1st Half - 1X2",
                        "P": "101",
                        "VW": "0",
                        "CNT": "GR",
                        "CNTLABEL": "Generic Result",
                        "GCAT": "HT",
                        "SV": null,
                        "SGN": [
                            "1",
                            "X",
                            "2"
                        ],
                        "SGNK": [
                            "1",
                            "X",
                            "2"
                        ],
                        "transKeys": {
                            "marketNameKey": "M#S_1X21T.NAME",
                            "marketDescKey": "M#S_1X21T.DESC",
                            "signs": {
                                "1": "MCU#S_1X21T_1",
                                "2": "MCU#S_1X21T_2",
                                "X": "MCU#S_1X21T_X"
                            }
                        }
                    },
                    {
                        "ID": "S_DC1T",
                        "NAME": "1st Half - Double Chance",
                        "P": "102",
                        "VW": "0",
                        "CNT": "GR",
                        "CNTLABEL": "Generic Result",
                        "GCAT": "HT",
                        "SV": null,
                        "SGN": [
                            "1X",
                            "12",
                            "X2"
                        ],
                        "SGNK": [
                            "1X",
                            "12",
                            "X2"
                        ],
                        "transKeys": {
                            "marketNameKey": "M#S_DC1T.NAME",
                            "marketDescKey": "M#S_DC1T.DESC",
                            "signs": {
                                "12": "MCU#S_DC1T_12",
                                "1X": "MCU#S_DC1T_1X",
                                "X2": "MCU#S_DC1T_X2"
                            }
                        }
                    },
                    {
                        "ID": "S_GOALS1T",
                        "NAME": "1st Half - Total Goals",
                        "P": "106",
                        "VW": "0",
                        "CNT": "G",
                        "CNTLABEL": "Goals",
                        "GCAT": "HT",
                        "SV": null,
                        "SGN": [
                            "1",
                            "2",
                            "3"
                        ],
                        "SGNK": [
                            "1",
                            "2",
                            "3"
                        ],
                        "transKeys": {
                            "marketNameKey": "M#S_GOALS1T.NAME",
                            "marketDescKey": "M#S_GOALS1T.DESC",
                            "signs": {
                                "1": "MCU#S_GOALS1T_1",
                                "2": "MCU#S_GOALS1T_2",
                                "3": "MCU#S_GOALS1T_3"
                            }
                        }
                    },
                    {
                        "ID": "S_OE",
                        "NAME": "Odd/Even",
                        "P": "6",
                        "VW": "0",
                        "CNT": "G",
                        "CNTLABEL": "Goals",
                        "GCAT": "POPULAR",
                        "SV": null,
                        "SGN": [
                            "Odd",
                            "Even"
                        ],
                        "SGNK": [
                            "OD",
                            "EV"
                        ],
                        "transKeys": {
                            "marketNameKey": "M#S_OE.NAME",
                            "marketDescKey": "M#S_OE.DESC",
                            "signs": {
                                "OD": "MCU#S_OE_OD",
                                "EV": "MCU#S_OE_EV"
                            }
                        }
                    }
                ]
            }
        },
        "TRANS": {
            "M#S_1X2": {
                "NAME": "1X2",
                "DESC": "You have to predict the outcome of the match in 90 minutes. The bet offers three possible outcomes: 1 (home team wins the match); X (teams draw), 2 (away team wins the match)"
            },
            "M#S_1X2_1": "1",
            "MCU#S_1X2_1": "{T1}",
            "M#S_1X2_X": "X",
            "MCU#S_1X2_X": "Draw",
            "M#S_1X2_2": "2",
            "MCU#S_1X2_2": "{T2}",
            "M#S_DC": {
                "NAME": "Double Chance",
                "DESC": "You have to predict the outcome of the match. There are 3 possible outcomes: 1X (at the end of the match the home team wins or draws), X2 (at the end of the match the away team wins or draws), 12 (at the end of the match the home team wins or the away team wins)."
            },
            "M#S_DC_1X": "1X",
            "MCU#S_DC_1X": "{T1} Or Draw",
            "M#S_DC_12": "12",
            "MCU#S_DC_12": "{T1} Or {T2}",
            "M#S_DC_X2": "X2",
            "MCU#S_DC_X2": "Draw Or {T2}",
            "M#S_OU": {
                "NAME": "Over / Under",
                "DESC": "Will the match have more or less goals than the allotted Total line at Full time (FT)"
            },
            "MH#S_OU": "Over|Under",
            "M#S_OU_O": "Over",
            "MCU#S_OU_O": "Over ({HND}) Goals",
            "M#S_OU_U": "Under",
            "MCU#S_OU_U": "Under ({HND}) Goals",
            "M#S_1X21T": {
                "NAME": "1st Half - 1X2",
                "DESC": "What will the result be at Half time (HT)?"
            },
            "M#S_1X21T_1": "1",
            "MCU#S_1X21T_1": "{T1}",
            "M#S_1X21T_X": "X",
            "MCU#S_1X21T_X": "Draw",
            "M#S_1X21T_2": "2",
            "MCU#S_1X21T_2": "{T2}",
            "M#S_DC1T": {
                "NAME": "1st Half - Double Chance",
                "DESC": "You have to predict the outcome of the first half time of the match: 1X, X2, 12"
            },
            "M#S_DC1T_1X": "1X",
            "MCU#S_DC1T_1X": "{T1} Or Draw",
            "M#S_DC1T_12": "12",
            "MCU#S_DC1T_12": "{T1} Or {T2}",
            "M#S_DC1T_X2": "X2",
            "MCU#S_DC1T_X2": "Draw Or {T2}",
            "M#S_GOALS1T": {
                "NAME": "1st Half - Total Goals",
                "DESC": "The total number of goals scored in the first half."
            },
            "M#S_GOALS1T_1": "1",
            "MCU#S_GOALS1T_1": "1",
            "M#S_GOALS1T_2": "2",
            "MCU#S_GOALS1T_2": "2",
            "M#S_GOALS1T_3": "3",
            "MCU#S_GOALS1T_3": "3",
            "M#S_OE": {
                "NAME": "Odd/Even",
                "DESC": "Odd or even total number of goals after Full time (FT)"
            },
            "M#S_OE_OD": "Odd",
            "MCU#S_OE_OD": "Odd",
            "M#S_OE_EV": "Even",
            "MCU#S_OE_EV": "Even"
        }
    }
}



not found will give this:

{
    "R": "OK",
    "D": {
        "numFound": 0,
        "start": 0
    }
}