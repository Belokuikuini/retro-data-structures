import json
import logging
import os
import pathlib

import construct
from retro_data_structures.asset_manager import AssetManager, IsoFileProvider
from retro_data_structures.formats.ancs import Ancs
from retro_data_structures.formats.mlvl import Mlvl
import pytest
import warnings
import nod
from retro_data_structures.game_check import Game



area_names = [
    ('Temple Grounds', 'Landing Site'), ('Temple Grounds', 'Service Access'), ('Temple Grounds', 'Hive Access Tunnel'), ('Temple Grounds', 'Path of Honor'), ('Temple Grounds', 'Meeting Grounds'), ('Temple Grounds', 'Hive Transport Area'), ('Temple Grounds', 'Hive Chamber A'), ('Temple Grounds', 'Hall of Honored Dead'), ('Temple Grounds', 'Hall of Eyes'), ('Temple Grounds', 'Temple Transport C'), ('Temple Grounds', 'Industrial Site'), ('Temple Grounds', 'Hive Chamber C'), ('Temple Grounds', 'Hive Tunnel'), ('Temple Grounds', 'Base Access'), ('Temple Grounds', 'Path of Eyes'), ('Temple Grounds', 'Agon Transport Access'), ('Temple Grounds', 'Collapsed Tunnel'), ('Temple Grounds', 'Hive Chamber B'), ('Temple Grounds', 'Hive Save Station'), ('Temple Grounds', 'Command Chamber'), ('Temple Grounds', 'War Ritual Grounds'), ('Temple Grounds', 'Abandoned Base'), ('Temple Grounds', 'Windchamber Gateway'), ('Temple Grounds', 'Torvus Transport Access'), ('Temple Grounds', 'Transport to Agon Wastes'), ('Temple Grounds', 'Temple Assembly Site'), ('Temple Grounds', 'Hive Storage'), ('Temple Grounds', 
'Portal Site'), ('Temple Grounds', 'Shrine Access'), ('Temple Grounds', 'Grand Windchamber'), ('Temple Grounds', 'Transport to Torvus Bog'), ('Temple Grounds', 'Dynamo Chamber'), ('Temple Grounds', 'Temple Transport B'), ('Temple Grounds', 'Storage Cavern B'), ('Temple Grounds', 'Plain of Dark Worship'), ('Temple Grounds', 'Defiled Shrine'), ('Temple Grounds', 'Gateway Access'), ('Temple Grounds', 'Windchamber Tunnel'), ('Temple Grounds', 'Ing Windchamber'), ('Temple Grounds', 'Communication Area'), ('Temple Grounds', 'Lake Access'), ('Temple Grounds', '!!00_scandummy'), ('Temple Grounds', 'Sky Temple Gateway'), ('Temple Grounds', 'GFMC Compound'), ('Temple Grounds', 'Storage Cavern A'), ('Temple Grounds', 'Trooper Security Station'), ('Temple Grounds', 'Accursed Lake'), ('Temple Grounds', '!!game_end_part1'), ('Temple Grounds', 'Fortress Transport Access'), ('Temple Grounds', 'Sacred Bridge'), ('Temple Grounds', '!!game_end_part2'), ('Temple Grounds', 'Transport to Sanctuary Fortress'), ('Temple Grounds', 'Sacred Path'), ('Temple Grounds', '!!game_end_part3'), ('Temple Grounds', 'Temple Transport A'), ('Temple Grounds', 'Profane Path'), ('Temple Grounds', '!!game_end_part4'), ('Temple Grounds', 'Phazon Pit'), ('Temple Grounds', '!!game_end_part5'), ('Temple Grounds', 'Phazon Grounds'), ('Temple Grounds', 'Reliquary Access'), ('Temple Grounds', 'Reliquary Grounds'), ('Temple Grounds', 'Ing Reliquary'), ('Great Temple', 'Temple Transport A'), ('Great Temple', 'Transport A Access'), ('Great Temple', 'Temple Sanctuary'), ('Great Temple', 'Transport C Access'), ('Great Temple', 'Controller Transport'), ('Great Temple', 'Transport B Access'), ('Great Temple', 'Temple Transport C'), ('Great Temple', 'Main Energy Controller'), ('Great Temple', 'Temple Transport B'), ('Great Temple', 'Sky Temple Energy Controller'), ('Great Temple', 'Sanctum Access'), ('Great Temple', 'Sanctum'), ('Agon Wastes', 'Transport to Temple Grounds'), ('Agon Wastes', 'Plaza Access'), ('Agon Wastes', 'Mining Plaza'), ('Agon Wastes', 'Agon Map Station'), ('Agon Wastes', 'Transit Station'), ('Agon Wastes', 'Save Station A'), ('Agon Wastes', 'Mining Station Access'), ('Agon Wastes', 'Duelling Range'), ('Agon Wastes', 'Mining Station B'), ('Agon Wastes', 'Transport Center'), ('Agon Wastes', 'Mining Station A'), ('Agon Wastes', 'Dark Transit Station'), ('Agon Wastes', 'Save Station 2'), ('Agon Wastes', 'Ing Cache 4'), ('Agon Wastes', 'Junction Site'), ('Agon Wastes', 'Storage A'), ('Agon Wastes', 'Mine Shaft'), ('Agon Wastes', 'Trial Grounds'), ('Agon Wastes', 'Portal Terminal'), ('Agon Wastes', 'Transport to Torvus Bog'), ('Agon Wastes', 'Crossroads'), ('Agon Wastes', 'Temple Access'), ('Agon Wastes', 'Central Station Access'), ('Agon Wastes', 'Sand Cache'), ('Agon Wastes', 'Portal Access A'), ('Agon Wastes', 'Judgment Pit'), ('Agon Wastes', 'Agon Temple'), ('Agon Wastes', 'Trial Tunnel'), ('Agon Wastes', 'Portal Site'), ('Agon Wastes', 'Central Mining Station'), ('Agon Wastes', 'Dark Agon Temple Access'), ('Agon Wastes', "Warrior's Walk"), ('Agon Wastes', 'Save Station 1'), ('Agon Wastes', 'Portal Access'), ('Agon Wastes', 'Controller Access'), ('Agon Wastes', 'Sandcanyon'), ('Agon Wastes', 'Dark Agon Temple'), ('Agon Wastes', 'Command Center Access'), ('Agon Wastes', 'Battleground'), ('Agon Wastes', 'Agon Energy Controller'), ('Agon Wastes', 'Ventilation Area A'), ('Agon Wastes', 'Dark Controller Access'), ('Agon Wastes', 'Command Center'), ('Agon Wastes', 'Double Path'), ('Agon Wastes', 'Main Energy Controller'), ('Agon Wastes', 'Transport to Sanctuary Fortress'), ('Agon Wastes', 'Main Reactor'), ('Agon Wastes', 'Dark Agon Energy Controller'), ('Agon Wastes', 'Biostorage Access'), ('Agon Wastes', 'Security Station B'), ('Agon Wastes', 'Doomed Entry'), ('Agon Wastes', 'Sand Processing'), ('Agon Wastes', 'Storage D'), ('Agon Wastes', 'Dark Oasis'), ('Agon Wastes', 'Biostorage Station'), ('Agon Wastes', 'Feeding Pit Access'), ('Agon Wastes', 'Oasis Access'), ('Agon Wastes', 'Save Station C'), ('Agon Wastes', 'Hall of Stairs'), ('Agon Wastes', 'Ing Cache 3'), ('Agon Wastes', 'Security Station A'), ('Agon Wastes', 'Storage B'), ('Agon Wastes', 'Feeding Pit'), ('Agon Wastes', 'Ventilation Area B'), ('Agon Wastes', 'Save Station 3'), ('Agon Wastes', 'Bioenergy Production'), ('Agon Wastes', 'Watering Hole'), ('Agon Wastes', 'Ing Cache 1'), ('Agon Wastes', 'Bitter Well'), ('Agon Wastes', 'Storage C'), ('Agon Wastes', 'Phazon Site'), ('Agon Wastes', 'Ing Cache 2'), ('Torvus Bog', 'Transport to Temple Grounds'), ('Torvus Bog', 'Temple Transport Access'), ('Torvus Bog', 'Torvus Lagoon'), ('Torvus Bog', 'Ruined Alcove'), ('Torvus Bog', 'Portal Chamber'), ('Torvus Bog', 'Path of Roots'), ('Torvus Bog', 'Save Station A'), ('Torvus Bog', 'Forgotten Bridge'), ('Torvus Bog', 'Portal Chamber'), ('Torvus Bog', 'Great Bridge'), ('Torvus Bog', 'Cache A'), ('Torvus Bog', 'Plaza Access'), ('Torvus Bog', 'Abandoned Worksite'), ('Torvus Bog', 'Dark Forgotten Bridge'), ('Torvus Bog', 'Grove Access'), ('Torvus Bog', 'Poisoned Bog'), ('Torvus Bog', 'Venomous Pond'), ('Torvus Bog', 'Temple Access'), ('Torvus Bog', 'Torvus Map Station'), ('Torvus Bog', 'Torvus Plaza'), ('Torvus Bog', 'Dark Arena Tunnel'), ('Torvus Bog', 'Putrid Alcove'), ('Torvus Bog', 'Brooding Ground'), ('Torvus Bog', 'Dark Falls'), ('Torvus Bog', 'Torvus Grove'), ('Torvus Bog', 'Dark Torvus Temple Access'), ('Torvus Bog', 'Save Station 1'), ('Torvus Bog', 'Torvus Temple'), ('Torvus Bog', 'Dark Torvus Arena'), ('Torvus Bog', 'Polluted Mire'), ('Torvus Bog', 'Underground Tunnel'), ('Torvus Bog', 'Meditation Vista'), 
('Torvus Bog', 'Dark Torvus Temple'), ('Torvus Bog', 'Transport to Agon Wastes'), ('Torvus Bog', 'Underground Transport'), ('Torvus Bog', 'Controller Access'), ('Torvus Bog', 'Gloom Vista'), ('Torvus Bog', 'Ammo Station'), ('Torvus Bog', 'Cache B'), ('Torvus Bog', 'Dark Controller Access'), ('Torvus Bog', 'Hydrodynamo Station'), ('Torvus Bog', 'Torvus Energy Controller'), ('Torvus Bog', 'Undertemple Shaft'), ('Torvus Bog', 'Dark Torvus Energy Controller'), ('Torvus Bog', 'Gathering Access'), ('Torvus Bog', 'Training Access'), ('Torvus Bog', 'Catacombs Access'), ('Torvus Bog', 'Save Station B'), ('Torvus Bog', 'Hydrodynamo Shaft'), ('Torvus Bog', 'Main Energy Controller'), ('Torvus Bog', 'Crypt Tunnel'), ('Torvus Bog', 'Sacrificial Chamber Tunnel'), ('Torvus Bog', 'Save Station 2'), ('Torvus Bog', 'Undertemple Access'), ('Torvus Bog', 'Gathering Hall'), ('Torvus Bog', 'Training Chamber'), ('Torvus Bog', 'Catacombs'), ('Torvus Bog', 'Main Hydrochamber'), ('Torvus Bog', 'Crypt'), ('Torvus Bog', 'Sacrificial Chamber'), ('Torvus Bog', 'Undertemple'), ('Torvus Bog', 'Transit Tunnel South'), ('Torvus Bog', 'Transit Tunnel West'), ('Torvus Bog', 'Transit Tunnel East'), ('Torvus Bog', 'Fortress Transport Access'), ('Torvus Bog', 'Dungeon'), ('Torvus Bog', 'Hydrochamber Storage'), ('Torvus Bog', 'Undertransit One'), ('Torvus Bog', 'Undertransit Two'), ('Torvus Bog', 'Transport to Sanctuary Fortress'), ('Sanctuary Fortress', 'Transport to Temple Grounds'), ('Sanctuary Fortress', 'Temple Transport Access'), ('Sanctuary Fortress', 'Sanctuary Entrance'), ('Sanctuary Fortress', 'Power Junction'), ('Sanctuary Fortress', 'Reactor Access'), ('Sanctuary Fortress', 'Reactor Core'), ('Sanctuary Fortress', 'Save Station A'), ('Sanctuary Fortress', 'Minigyro Chamber'), ('Sanctuary Fortress', 
'Transit Station'), ('Sanctuary Fortress', 'Sanctuary Map Station'), ('Sanctuary Fortress', 'Hall of Combat Mastery'), ('Sanctuary Fortress', 'Main Research'), ('Sanctuary Fortress', 'Hive Portal Chamber'), ('Sanctuary Fortress', 'Agon Transport Access'), ('Sanctuary Fortress', 'Central Area Transport East'), ('Sanctuary Fortress', 'Culling Chamber'), ('Sanctuary Fortress', 'Central Area Transport West'), ('Sanctuary Fortress', 'Torvus Transport Access'), ('Sanctuary Fortress', 'Staging Area'), ('Sanctuary Fortress', 'Transport to Agon Wastes'), ('Sanctuary Fortress', 'Dynamo Works'), ('Sanctuary Fortress', 'Hazing Cliff'), ('Sanctuary Fortress', 'Central Hive East Transport'), ('Sanctuary Fortress', 'Unseen Way'), ('Sanctuary Fortress', 'Watch Station'), ('Sanctuary Fortress', 'Transport to Torvus Bog'), ('Sanctuary Fortress', 'Central Hive West Transport'), ('Sanctuary Fortress', 'Dynamo Access'), ('Sanctuary Fortress', 'Workers Path'), ('Sanctuary Fortress', 'Dynamo Storage'), ('Sanctuary Fortress', 'Hive Dynamo Works'), ('Sanctuary Fortress', 'Hive Reactor'), ('Sanctuary Fortress', "Sentinel's Path"), ('Sanctuary Fortress', 'Watch Station Access'), ('Sanctuary Fortress', 'Grand Abyss'), ('Sanctuary Fortress', 'Aerial Training Site'), ('Sanctuary Fortress', 'Main Gyro Chamber'), ('Sanctuary Fortress', 'Sanctuary Temple'), ('Sanctuary Fortress', 'Hive Cache 3'), ('Sanctuary Fortress', 'Hive Dynamo Access'), ('Sanctuary Fortress', 'Hive Save Station 1'), ('Sanctuary Fortress', 'Hive Reactor Access'), ('Sanctuary Fortress', 'Hive Cache 1'), ('Sanctuary Fortress', 'Judgment Drop'), ('Sanctuary Fortress', 'Vault'), ('Sanctuary Fortress', 'Temple Security Access'), ('Sanctuary Fortress', 'Temple Access'), ('Sanctuary Fortress', 'Checkpoint Station'), ('Sanctuary Fortress', 'Save Station B'), ('Sanctuary Fortress', 'Controller Access'), ('Sanctuary Fortress', 'Hive Gyro Chamber'), ('Sanctuary Fortress', 'Entrance Defense Hall'), ('Sanctuary Fortress', 'Vault Attack Portal'), ('Sanctuary Fortress', 'Hive Temple'), ('Sanctuary Fortress', 'Aerie Transport Station'), ('Sanctuary Fortress', 'Sanctuary Energy Controller'), ('Sanctuary Fortress', 'Hive Temple Access'), ('Sanctuary Fortress', 'Hive Gyro Access'), ('Sanctuary Fortress', 'Hive Save Station 2'), ('Sanctuary Fortress', 'Hive Entrance'), ('Sanctuary Fortress', 'Hive Controller Access'), ('Sanctuary Fortress', 'Aerie Access'), ('Sanctuary Fortress', 'Main Energy Controller'), ('Sanctuary Fortress', 'Hive Ammo Station'), ('Sanctuary Fortress', 'Hive Energy Controller'), ('Sanctuary Fortress', 'Aerie'), ('Sanctuary Fortress', 'Hive Summit')]

areas = {'Temple Grounds': {'Landing Site': (1006255871, 1655756413), 'Service Access': (1006255871, 2679590972), 'Hive Access Tunnel': (1006255871, 2970881060), 'Path of Honor': (1006255871, 2068656603), 'Meeting Grounds': (1006255871, 2606692981), 'Hive Transport Area': (1006255871, 2485094202), 'Hive Chamber A': (1006255871, 1353937573), 'Hall of Honored Dead': (1006255871, 3098756660), 'Hall of Eyes': (1006255871, 1198237772), 'Temple Transport C': (1006255871, 2918020398), 'Industrial Site': (1006255871, 1655474884), 'Hive Chamber C': (1006255871, 4219746340), 'Hive Tunnel': (1006255871, 360901706), 'Base Access': (1006255871, 1752128027), 'Path of Eyes': (1006255871, 3997643454), 'Agon Transport Access': (1006255871, 2744240555), 'Collapsed Tunnel': (1006255871, 1536348486), 'Hive Chamber B': (1006255871, 494654382), 'Hive Save Station': (1006255871, 341957679), 'Command Chamber': (1006255871, 3592880139), 'War Ritual Grounds': (1006255871, 2859985581), 'Abandoned Base': (1006255871, 3337937090), 'Windchamber Gateway': (1006255871, 1966181726), 'Torvus Transport Access': (1006255871, 2822315693), 'Transport to Agon Wastes': (1006255871, 1660916974), 'Temple Assembly Site': (1006255871, 1263425809), 'Hive Storage': (1006255871, 1667749239), 'Portal Site': (1006255871, 3661102999), 'Shrine Access': (1006255871, 521996255), 'Grand Windchamber': (1006255871, 2909835645), 'Transport to Torvus Bog': (1006255871, 2889020216), 'Dynamo Chamber': (1006255871, 3032508327), 'Temple Transport B': (1006255871, 1287880522), 'Storage Cavern B': (1006255871, 3197418796), 'Plain of Dark Worship': (1006255871, 67496868), 'Defiled Shrine': (1006255871, 383850164), 'Gateway Access': (1006255871, 2217888920), 'Windchamber Tunnel': (1006255871, 2590194623), 'Ing Windchamber': (1006255871, 3455003633), 'Communication Area': (1006255871, 1667141025), 'Lake Access': (1006255871, 1753921710), '!!00_scandummy': (1006255871, 320615304), 'Sky Temple Gateway': (1006255871, 2278776548), 'GFMC Compound': (1006255871, 1467316949), 'Storage Cavern A': (1006255871, 939577218), 'Trooper Security Station': (1006255871, 1441689027), 'Accursed Lake': (1006255871, 2681312991), '!!game_end_part1': (1006255871, 517527729), 'Fortress Transport Access': (1006255871, 1894115037), 'Sacred Bridge': (1006255871, 3132939042), '!!game_end_part2': (1006255871, 2555161119), 'Transport to Sanctuary Fortress': (1006255871, 3455543403), 'Sacred Path': (1006255871, 3258777533), '!!game_end_part3': (1006255871, 1393588666), 'Temple Transport A': (1006255871, 1345979968), 'Profane Path': (1006255871, 1692811478), '!!game_end_part4': (1006255871, 1310017794), 'Phazon Pit': (1006255871, 506667008), '!!game_end_part5': (1006255871, 2236193447), 'Phazon Grounds': (1006255871, 1683944003), 'Reliquary Access': (1006255871, 2235615956), 'Reliquary Grounds': (1006255871, 4237279396), 'Ing Reliquary': (1006255871, 1956545251)}, 'Great Temple': {'Temple Transport A': (2252328306, 408633584), 'Transport A Access': (2252328306, 3885674414), 'Temple Sanctuary': (2252328306, 2731245106), 'Transport C Access': (2252328306, 441310400), 'Controller Transport': (2252328306, 300223430), 'Transport B Access': (2252328306, 4273454375), 'Temple Transport C': (2252328306, 2556480432), 'Main Energy Controller': (2252328306, 44045108), 'Temple Transport B': (2252328306, 2399252740), 'Sky Temple Energy Controller': (2252328306, 2068511343), 'Sanctum Access': (2252328306, 3417147547), 'Sanctum': (2252328306, 3619928121)}, 'Agon Wastes': {'Transport to Temple Grounds': (1119434212, 1473133138), 'Plaza Access': (1119434212, 2918746407), 'Mining Plaza': (1119434212, 1115663770), 'Agon Map Station': (1119434212, 2220656039), 'Transit Station': (1119434212, 2043266464), 'Save Station A': (1119434212, 1342271826), 'Mining Station Access': (1119434212, 2373615500), 'Duelling Range': (1119434212, 1063051065), 'Mining Station B': (1119434212, 3682282733), 'Transport Center': (1119434212, 1272952761), 'Mining Station A': (1119434212, 3820941951), 'Dark Transit Station': (1119434212, 3611217256), 'Save Station 2': (1119434212, 2887798667), 'Ing Cache 4': (1119434212, 3318204883), 'Junction Site': (1119434212, 369673571), 'Storage A': (1119434212, 271726916), 'Mine Shaft': (1119434212, 3617674289), 'Trial Grounds': (1119434212, 2260839223), 'Portal Terminal': (1119434212, 734872743), 'Transport to Torvus Bog': (1119434212, 2806956034), 'Crossroads': (1119434212, 2384714559), 'Temple Access': (1119434212, 710454340), 'Central Station Access': (1119434212, 4268351683), 'Sand Cache': (1119434212, 4105303847), 'Portal Access A': (1119434212, 588443165), 'Judgment Pit': (1119434212, 1803024829), 'Agon Temple': (1119434212, 1979488942), 'Trial Tunnel': (1119434212, 1222921974), 'Portal Site': (1119434212, 3212793644), 'Central Mining Station': (1119434212, 4121352562), 'Dark Agon Temple Access': (1119434212, 553896110), "Warrior's Walk": (1119434212, 872074261), 'Save Station 1': (1119434212, 1511345710), 'Portal Access': (1119434212, 2312259325), 'Controller Access': (1119434212, 3209927104), 'Sandcanyon': (1119434212, 3853985320), 'Dark Agon Temple': (1119434212, 1970603146), 'Command Center Access': (1119434212, 1887668217), 'Battleground': (1119434212, 3933819436), 'Agon Energy Controller': (1119434212, 50083607), 'Ventilation Area A': (1119434212, 2217754069), 'Dark Controller Access': (1119434212, 2733852625), 'Command Center': (1119434212, 834819415), 'Double Path': (1119434212, 2146386747), 'Main Energy Controller': (1119434212, 3643314371), 'Transport to Sanctuary Fortress': (1119434212, 3331021649), 'Main Reactor': (1119434212, 3436835742), 'Dark Agon Energy Controller': (1119434212, 3084730374), 'Biostorage Access': (1119434212, 3739948648), 'Security Station B': (1119434212, 182082287), 'Doomed Entry': (1119434212, 2761919085), 'Sand Processing': (1119434212, 2763180926), 'Storage D': (1119434212, 1090496759), 'Dark Oasis': (1119434212, 2583401855), 'Biostorage Station': (1119434212, 2156489961), 'Feeding Pit Access': (1119434212, 3761619109), 'Oasis Access': (1119434212, 4073505822), 'Save Station C': (1119434212, 3111736876), 'Hall of Stairs': (1119434212, 1830176640), 'Ing Cache 3': (1119434212, 3122914805), 'Security Station A': (1119434212, 4146307738), 'Storage B': (1119434212, 2527480810), 'Feeding Pit': (1119434212, 123369195), 'Ventilation Area B': (1119434212, 1498100491), 'Save Station 3': (1119434212, 41547759), 'Bioenergy Production': (1119434212, 323423656), 'Watering Hole': (1119434212, 2603303494), 'Ing Cache 1': (1119434212, 1385574326), 'Bitter Well': (1119434212, 82952664), 'Storage C': (1119434212, 1576704079), 'Phazon Site': (1119434212, 537851367), 'Ing Cache 2': (1119434212, 2467885174)}, 'Torvus Bog': {'Transport to Temple Grounds': (1039999561, 1868895730), 'Temple Transport Access': (1039999561, 668125336), 'Torvus Lagoon': (1039999561, 2114709145), 'Ruined Alcove': (1039999561, 3548128276), 'Portal Chamber': 
(1039999561, 2921206585), 'Path of Roots': (1039999561, 1950913308), 'Save Station A': (1039999561, 3681435765), 'Forgotten Bridge': (1039999561, 165596961), 'Great Bridge': (1039999561, 3822429534), 'Cache A': (1039999561, 212528838), 'Plaza Access': (1039999561, 3250751238), 'Abandoned Worksite': (1039999561, 1423634263), 'Dark Forgotten Bridge': (1039999561, 39024685), 'Grove Access': (1039999561, 1180978245), 'Poisoned Bog': (1039999561, 350405542), 'Venomous Pond': (1039999561, 2240736467), 'Temple Access': (1039999561, 121681107), 'Torvus Map Station': (1039999561, 673929343), 'Torvus Plaza': (1039999561, 1978751231), 'Dark Arena Tunnel': (1039999561, 957217977), 'Putrid Alcove': (1039999561, 3418828153), 'Brooding Ground': (1039999561, 3706669497), 'Dark Falls': (1039999561, 774215801), 'Torvus Grove': (1039999561, 3896048152), 'Dark Torvus Temple Access': (1039999561, 3851937017), 'Save Station 1': (1039999561, 2591519810), 'Torvus Temple': (1039999561, 3863006870), 'Dark Torvus Arena': (1039999561, 2761578287), 'Polluted Mire': (1039999561, 2208154870), 'Underground Tunnel': (1039999561, 2162589584), 'Meditation Vista': (1039999561, 1576678107), 'Dark Torvus Temple': (1039999561, 912503189), 'Transport to Agon Wastes': (1039999561, 3479543630), 'Underground Transport': (1039999561, 2455297154), 'Controller Access': (1039999561, 720788297), 'Gloom Vista': (1039999561, 2504558791), 'Ammo Station': (1039999561, 2258105898), 'Cache B': (1039999561, 7688697), 'Dark Controller Access': (1039999561, 298078827), 'Hydrodynamo Station': (1039999561, 
3585454182), 'Torvus Energy Controller': (1039999561, 322696632), 'Undertemple Shaft': (1039999561, 3000230508), 'Dark Torvus Energy Controller': (1039999561, 1591201049), 'Gathering Access': (1039999561, 1393426305), 'Training Access': (1039999561, 2007998417), 'Catacombs Access': (1039999561, 2999623881), 'Save Station B': (1039999561, 3407240152), 'Hydrodynamo Shaft': (1039999561, 813912549), 'Main Energy Controller': (1039999561, 2793419525), 'Crypt Tunnel': (1039999561, 1304699309), 'Sacrificial Chamber Tunnel': (1039999561, 1709535693), 'Save Station 2': (1039999561, 321212102), 'Undertemple Access': (1039999561, 700027128), 'Gathering Hall': (1039999561, 889276218), 'Training Chamber': (1039999561, 1270197856), 'Catacombs': (1039999561, 4217540043), 'Main Hydrochamber': (1039999561, 3468345533), 'Crypt': (1039999561, 3366472600), 'Sacrificial Chamber': (1039999561, 1654100212), 'Undertemple': (1039999561, 2242084895), 'Transit Tunnel South': (1039999561, 3072694950), 'Transit Tunnel West': (1039999561, 3780180813), 'Transit Tunnel East': (1039999561, 1727410190), 'Fortress Transport Access': (1039999561, 1662585441), 'Dungeon': (1039999561, 3152327598), 'Hydrochamber Storage': (1039999561, 2527519102), 'Undertransit One': (1039999561, 1557447417), 'Undertransit Two': (1039999561, 1274848825), 'Transport to Sanctuary Fortress': (1039999561, 3205424168)}, 'Sanctuary Fortress': {'Transport to Temple Grounds': (464164546, 3528156989), 'Temple Transport Access': (464164546, 1650075282), 'Sanctuary Entrance': (464164546, 1193696267), 'Power Junction': (464164546, 834698518), 'Reactor Access': (464164546, 3060184661), 'Reactor Core': (464164546, 1248653973), 'Save Station A': (464164546, 1706557902), 'Minigyro Chamber': (464164546, 2532624926), 'Transit Station': (464164546, 4148317891), 'Sanctuary Map Station': (464164546, 1388284403), 'Hall of Combat Mastery': (464164546, 1433528478), 'Main Research': (464164546, 2437878657), 'Hive Portal Chamber': (464164546, 2073342059), 'Agon Transport Access': (464164546, 1963704303), 'Central Area Transport East': (464164546, 290586973), 'Culling Chamber': (464164546, 1762359402), 'Central Area Transport West': (464164546, 1894024576), 'Torvus Transport Access': (464164546, 4071453868), 'Staging Area': (464164546, 1539257167), 'Transport to Agon Wastes': (464164546, 900285955), 'Dynamo Works': (464164546, 3222355176), 'Hazing Cliff': (464164546, 931221290), 'Central Hive East Transport': (464164546, 3268908651), 'Unseen Way': (464164546, 3590320811), 'Watch Station': (464164546, 2722128775), 'Transport to Torvus Bog': (464164546, 3145160350), 'Central Hive West Transport': (464164546, 1824314539), 'Dynamo Access': (464164546, 1120426713), 'Workers Path': (464164546, 65839695), 'Dynamo Storage': (464164546, 527902968), 'Hive Dynamo Works': (464164546, 4065261236), 'Hive Reactor': (464164546, 4175151165), "Sentinel's Path": (464164546, 2765624647), 'Watch Station Access': (464164546, 1349974475), 'Grand Abyss': (464164546, 595516932), 'Aerial Training Site': (464164546, 1089946750), 'Main Gyro Chamber': (464164546, 1932798548), 'Sanctuary Temple': (464164546, 1815493844), 'Hive Cache 3': (464164546, 120573884), 'Hive Dynamo Access': (464164546, 4222565163), 'Hive Save Station 1': (464164546, 3143049775), 'Hive Reactor Access': (464164546, 2955332843), 'Hive Cache 1': (464164546, 1598256765), 'Judgment Drop': (464164546, 1438939627), 'Vault': (464164546, 1378173793), 'Temple Security Access': (464164546, 1122770219), 'Temple Access': (464164546, 3312357786), 'Checkpoint Station': (464164546, 2219469068), 'Save Station B': (464164546, 3811341152), 'Controller Access': (464164546, 3902528658), 'Hive Gyro Chamber': (464164546, 2741330578), 'Entrance Defense Hall': (464164546, 2802755627), 'Vault Attack Portal': (464164546, 502346057), 'Hive Temple': (464164546, 2838429875), 'Aerie Transport Station': (464164546, 3136899603), 'Sanctuary Energy Controller': (464164546, 218311274), 'Hive Temple Access': (464164546, 3968294891), 'Hive Gyro Access': (464164546, 657793899), 'Hive Save Station 2': (464164546, 582304814), 'Hive Entrance': (464164546, 4093264161), 'Hive Controller Access': (464164546, 648838942), 'Aerie Access': (464164546, 3741790551), 'Main Energy Controller': (464164546, 1460882882), 'Hive Ammo Station': (464164546, 4057954524), 'Hive Energy Controller': (464164546, 770491160), 'Aerie': (464164546, 1564082177), 'Hive Summit': (464164546, 2642430293)}}


missing = [
    ("Great Temple", "Transport A Access"),
    ("Great Temple", "Transport B Access"),
    ("Agon Wastes", "Portal Access"),
    ("Torvus Bog", "Dark Forgotten Bridge"),
    ("Torvus Bog", "Forgotten Bridge"),
    ("Torvus Bog", "Sacrificial Chamber"),
    ("Sanctuary Fortress", "Dynamo Works"),
    ("Sanctuary Fortress", "Hall of Combat Mastery"),
    ("Sanctuary Fortress", "Hive Portal Chamber"),
    ("Sanctuary Fortress", "Hive Reactor"),
    ("Sanctuary Fortress", "Reactor Access"),
    ("Agon Wastes", "Portal Terminal"),
    ("Agon Wastes", "Transport to Sanctuary Fortress"),
    ("Sanctuary Fortress", "Temple Transport Access"),
    ("Sanctuary Fortress", "Minigyro Chamber"),
    ("Sanctuary Fortress", "Staging Area"),
    ("Torvus Bog", "Dungeon"),
    ("Sanctuary Fortress", "Hive Temple"),
    ("Great Temple", "Sanctum")
]
def patch_missing_dependencies():
    iso = pathlib.Path("C:/Users/dunca/Downloads/echoes/Metroid Prime 2 - Echoes (USA).iso")
    prime2_asset_manager: AssetManager = AssetManager(IsoFileProvider(iso),
                        target_game=Game.ECHOES)

    callback1 = lambda name, prog: print(f"{prog*100}%: {name}")
    callback2 = lambda prog, name, _: print(f"{prog*100}%: {name}")
    files = pathlib.Path("C:/Users/dunca/Documents/Patched Echoes/Files")

    disc, _ = nod.open_disc_from_image(iso)
    data_partition = disc.get_data_partition()
    context = nod.ExtractionContext()
    context.set_progress_callback(callback1)
    data_partition.extract_to_directory(os.fspath(files), context)

    for world_name, area_name in missing:
        print(area_name)
        mlvl_id, mrea_id = areas[world_name][area_name]
        mlvl = prime2_asset_manager.get_file(mlvl_id, Mlvl)
        area = mlvl.get_area(mrea_id)
        area.build_mlvl_dependencies()
        prime2_asset_manager.replace_asset(mlvl_id, mlvl)

    prime2_asset_manager.save_modifications(files)
    disc_builder = nod.DiscBuilderGCN(
        files.parent.joinpath("echoes.iso"),
        callback2
    )
    disc_builder.build_from_directory(files)


def test_ancs_deps(prime2_asset_manager: AssetManager):
    mlvl_id, mrea_id, ancs_id = 0x3BFA3EFF, 0x64E640D6, 0x7587F0CD

    mlvl = prime2_asset_manager.get_file(mlvl_id, Mlvl)
    area = mlvl.get_area(mrea_id)
    ancs = prime2_asset_manager.get_file(ancs_id, Ancs)

    area_deps = set(area.get_layer("Default").dependencies)
    ancs_deps = set(ancs.dependencies_for(True, 0))

    construct.lib.setGlobalPrintFullStrings(True)
    print(ancs.raw)
    construct.lib.setGlobalPrintFullStrings(False)

    orphans = {(typ, hex(idx)) for typ, idx in ancs_deps.difference(area_deps)}
    assert orphans == set()


@pytest.mark.parametrize(["world_name", "area_name"], area_names)
# @pytest.mark.skip
def test_mlvl_dependencies(prime2_asset_manager: AssetManager, world_name, area_name):
    mlvl_id, mrea_id = areas[world_name][area_name]

    mlvl = prime2_asset_manager.get_file(mlvl_id, Mlvl)
    area = mlvl.get_area(mrea_id)

    area_identifier = f"{world_name} - {area_name}"
    print(area_identifier)


    old = area.dependencies
    old = {layer_name: set((typ, hex(idx)) for typ, idx in layer) for layer_name, layer in old.items()}
    area.build_mlvl_dependencies()
    new = area.dependencies
    new = {layer_name: set((typ, hex(idx)) for typ, idx in layer) for layer_name, layer in new.items()}

    orphaned_layers = False

    exc = f"Orphaned dependencies in {area_identifier}"

    for (layer_name, old_layer), new_layer in zip(old.items(), new.values()):
        orphans = set(old_layer).symmetric_difference(new_layer)
        orphaned_types = set(typ for typ, _ in orphans)

        if len(orphaned_types):
            # warnings.warn(f"{exc} layer {layer_name}: {orphaned_types}")
            orphaned_layers = True
    
    missing = {
        layer_name: old_layer.difference(new_layer)
        for (layer_name, old_layer), new_layer
        in zip(old.items(), new.values())
    }

    extra = {
        layer_name: new_layer.difference(old_layer)
        for (layer_name, old_layer), new_layer
        in zip(old.items(), new.values())
    }
    
    missing = {n: list(miss) for n, miss in missing.items() if miss}
    extra = {n: list(ext) for n, ext in extra.items() if ext}

    f = pathlib.Path(f"area_deps/{world_name}/{area_name}.json")
    if orphaned_layers:
        f.parent.parent.mkdir(exist_ok=True)
        f.parent.mkdir(exist_ok=True)
        f.touch()
        json.dump({"missing": missing, "extra": extra}, f.open("w"), indent=4)
    else:
        f.unlink(missing_ok=True)

    if len(extra):
        logging.warning(f"Extra dependencies leftover in {area_identifier}!")
    assert not len(missing)
    if len(extra):
        pytest.skip()
