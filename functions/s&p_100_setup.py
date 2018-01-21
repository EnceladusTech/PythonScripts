
def getSP100(context):
    return [
    sid(24),    # AAPL,  APPLE INC
    sid(43694), # ABBV
    sid(62),    # ABT,   ABBOTT LABORATORIES
    sid(25555), # ACN,   ACCENTURE PLC
    sid(205),   # AGN,
    #sid(161),   # AEP,   AMERICAN ELECTRIC POWER INC
    sid(239),   # AIG,   AMERICAN INTL GROUP INC
    sid(24838), # ALL,   ALLSTATE CORP (THE)
    sid(368),   # AMGN,  AMGEN INC
    sid(16841), # AMZN,  AMAZON.COM INC
    #sid(448),   # APA,   APACHE CORP
    #sid(455),   # APC,   ANADARKO PETROLEUM CORP
    sid(679),   # AXP,   AMERICAN EXPRESS COMPANY
    sid(698),   # BA,    BOEING CO
    sid(700),   # BAC,   BANK OF AMERICA CORP
    sid(3806),  #BIIB,
    #sid(734),   # BAX,   BAXTER INTERNATIONAL INC
    sid(903),   # BK,    BANK OF NEW YORK MELLON CORP/T
    sid(20689), # BLK,
    sid(980),   # BMY,   BRISTOL MYERS SQUIBB COMPANY
    sid(11100), # BRK.B, BERKSHIRE HATHWY INC(HLDG CO) B
    sid(1335),  # C,     CITIGROUP
    sid(1267),  # CAT,   CATERPILLAR INC
    sid(1406), # CELG,
    sid(20838), #CHTR,
    sid(1582),  # CL,    COLGATE-PALMOLIVE CO
    sid(1637), #CMCSA	Comcast Corporation
    sid(12160), # COF,   CAPITAL ONE FINANCIAL CORP
    sid(23998), # COP,   CONOCOPHILLIPS
    sid(1787),  # COST,  COSTCO WHOLESALE CORP
    sid(1900),  # CSCO,  CISCO SYSTEMS INC
    #sid(1971),  # CTS,   CTS CORP
    sid(4799),  # CVS,   CVS CAREMARK CORP
    sid(23112), # CVX,   CHEVRON CORPORATION
    #sid(2119),  # DD,    DU PONT DE NEMOURS E I &CO
    #sid(25317), # DELL,  DELL INC
    sid(2170),      # DHR	Danaher
    sid(2190),  # DIS,   WALT DISNEY CO-DISNEY COMMON
    sid(2351),      #DUK	Duke Energy
    sid(51157),      #DWDP	DowDuPont
    #sid(2263),  # DOW,   DOW CHEMICAL CO
    #sid(2368),  # DVN,   DEVON ENERGY CORP (NEW)
    #sid(24819), # EBAY,  EBAY INC
    #sid(2518),  # EMC,   EMC CORPORATION
    sid(2530),  # EMR,   EMERSON ELECTRIC CO
    sid(22114), # EXC,   EXELON CORPORATION
    sid(2673),  # F,     FORD MOTOR CO(NEW)
    sid(42950),  #FB	Facebook
    #sid(13197), # FCX,   FREEPORT-MCMORAN COPPER&GOLD B
    sid(2765),  # FDX,   FEDEX CORPORATION
    sid(5530),      #FOX	21st Century Fox
    sid(12213),      #FOXA	21st Century Fox
    sid(3136),  # GD,    GENERAL DYNAMICS CORP
    sid(3149),  # GE,    GENERAL ELECTRIC CO
    sid(3212),  # GILD,  GILEAD SCIENCES INC
    sid(3246),  # GM,    GENERAL MOTORS CORP
    sid(46631), # GOOG,  GOOGLE INC,
    sid(26578),      # GOOGL	Alphabet Inc
    sid(20088), # GS,    GOLDMAN SACHS GROUP INC
    sid(3443),  # HAL,   HALLIBURTON CO (HOLDING CO)
    sid(3496),  # HD,    HOME DEPOT INC
    sid(25090), # HON,   HONEYWELL INTERNATIONAL INC
    #sid(3735),  # HPQ,   HEWLETT-PACKARD CO
    sid(3766),  # IBM,   INTL BUSINESS MACHINES CORP
    sid(3951),  # INTC,  INTEL CORP
    sid(4151),  # JNJ,   JOHNSON AND JOHNSON
    sid(25006), # JPM,   JPMORGAN CHASE & CO COM STK
    sid(49229),      #KHC	Kraft Heinz
    sid(20744),      #KMI	Kinder Morgan Inc/DE **KMI has 2 ids in quantopia
    sid(40852),          #KMI Kinder Morgan Inc/DE *KMI has 2 ids in quantopia
    sid(4283),  # KO,    COCA-COLA CO
    sid(4487),  # LLY,   LILLY ELI & CO
    sid(12691), # LMT,   LOCKHEED MARTIN CORP
    sid(4521),  # LOW,   LOWES COMPANIES INC
    sid(32146), # MA,    MASTERCARD INC
    sid(4707),  # MCD,   MCDONALDS CORP
    sid(22802), # MDLZ,  MONDELEZ INTERNATIONAL INC
    sid(4758),  # MDT,   MEDTRONIC INC
    sid(21418), # MET,   METLIFE  INC
    sid(4922),  # MMM,   3M COMPANY
    sid(4954),  # MO,    ALTRIA GROUP INC.
    sid(22140), # MON,   MONSANTO COMPANY
    sid(5029),  # MRK,   MERCK & CO INC
    sid(17080), # MS,    MORGAN STANLEY
    sid(5061),  # MSFT,  MICROSOFT CORP
    sid(2968),      #NEE	NextEra Energy
    sid(5328),  # NKE,   NIKE INC CL-B
    #sid(24809), # NOV,   NATIONAL OILWELL VARCO  INC.
    #sid(5442),  # NSC,   NORFOLK SOUTHERN CORP
    #sid(12213), # NWSA,  NEWS CP - CL A
    sid(5692),  # ORCL,  ORACLE CORP
    sid(5729),  # OXY,   OCCIDENTAL PETROLEUM CORP
    sid(19917),      #PCLN	Priceline Group Inc/The
    sid(5885),  # PEP,   PEPSICO INC
    sid(5923),  # PFE,   PFIZER INC
    sid(5938),  # PG,    PROCTER & GAMBLE CO
    sid(35902), # PM,    PHILIP MORRIS INTERNATIONAL INC
    sid(49242),      #PYPL	PayPal Holdings
    sid(6295),  # QCOM,  QUALCOMM INC
    sid(6583),  # RTN,   RAYTHEON CO. (NEW)
    sid(6683),  # SBUX,  STARBUCKS CORPORATION
    sid(6928),  # SLB,   SCHLUMBERGER LTD
    sid(7011),  # SO,    SOUTHERN CO
    sid(10528), # SPG,   SIMON PROPERTIES GROUP INC
    sid(6653),  # T,     AT&T INC. COM
    sid(21090), # TGT,   TARGET CORPORATION
    sid(357),   # TWX,   TIME WARNER INC.
    sid(7671),  # TXN,   TEXAS INSTRUMENTS INC
    sid(7792),  # UNH,   UNITEDHEALTH GROUP INC
    sid(7800),  # UNP,   UNION PACIFIC CORPORATION
    sid(20940), # UPS,   UNITED PARCEL SERVICE INC.CL B
    sid(25010), # USB,   U.S.BANCORP (NEW)
    sid(7883),  # UTX,   UNITED TECHNOLOGIES CORP
    sid(35920), # V,     VISA INC
    sid(21839), # VZ,    VERIZON COMMUNICATIONS
    #sid(8089),  # WAG,   WALGREEN COMPANY
    sid(8089),       #WBA	Walgreens Boots Alliance
    sid(8151),  # WFC,   WELLS FARGO & CO(NEW)d
    #sid(8214),  # WMB,   WILLIAMS COMPANIES
    sid(8229),  # WMT,   WAL-MART STORES INC
    sid(8347),  # XOM,   EXXON MOBIL CORPORATION
    ]
