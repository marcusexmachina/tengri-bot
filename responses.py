"""
All bot responses — single source of truth. Add new variants to lists for rotating responses.
Handlers use get_response(key, **kwargs) for random selection and formatting.
"""
import random

# Spam & media flood
SPAM_WARNING_MESSAGES = [
    "Shut the fuck up {mention}, nigger—you're flooding this chat worse than your mom's crack pipe notifications",
    "Your text spam is pure terminal nigger NPC energy {mention}. Muted, retard—go touch grass instead of that cum-crusted keyboard",
    "Typing like a malfunctioning pajeet bot on bath salts {mention}. Muted, curry nigger. Come back when you can form a coherent thought, dipshit",
    "Chronic diarrhea of the fingers detected {mention}. Muted harder than your Jew dad wishes he aborted your worthless ass. Enjoy the void, spam goblin",
    "{mention} spamming so hard even Indian call center niggers are embarrassed for you. Muted for being a walking genetic dead-end",
    "Flooding the chat like a nigger shitting in the group pool {mention}. Muted, you absolute AIDS-ridden cancer",
    "Your spam barrage dropped the group's IQ lower than a nigger's credit score {mention}. Muted—develop a personality, you emoji-vomiting faggot",
    "Congrats {mention}, you've turned this chat into your personal Tel Aviv landfill. Muted. Next time I'll pray your entire bloodline gets cancer",
    "Your spam is so pathetic it's like watching a virgin Jew try to get laid {mention}—awkward, unwanted, and over in 3 seconds. Muted, you cum-guzzling foreskin remnant",
    "Flooding harder than your tears when mommy takes your welfare check {mention}. Muted, you braindead basement nigger",
    "Every message you send is a war crime against basic human decency {mention}. Muted—go choke on your own irrelevance, you worthless fuckwit",
    "You're the human equivalent of spyware made by pajeets {mention}: annoying, persistent, and nobody wants your shitty code. Muted, parasite",
    "Spam level: Hiroshima after the Jew dropped it {mention}. You've nuked the chat with your bullshit. Muted, you glowing radioactive trash",
    "If retardation was currency {mention}, your spam would make you richer than a Rothschild. Muted—bankrupt your retarded ass elsewhere, kike",
    "Your messages are like AIDS {mention}: they keep spreading and ruining everything. Muted, you infectious jungle monkey",
    "Even bots have more self-control than your trigger-happy nigger fingers {mention}. Muted—evolve or get genocided, subhuman",
    "You've spammed more garbage than a pajeet street shitter after Diwali {mention}. Muted, you diarrheal disaster",
    "This chat isn't your therapy session for being born a failure {mention}. Muted—cry to your absent father, you emotional black hole",
    "Spamming like a nigger with a free iPhone on payday {mention}. Muted—go loot somewhere else, pavement ape",
    "Your flood is more annoying than a Jew haggling over 2 cents {mention}. Muted, you hook-nosed cheapskate parasite",
    "Every post you make smells like curry, failure, and unwashed armpits {mention}. Muted, pajeet—take your spam back to the call center toilet",
    "You're shitting out messages faster than a nigger shits out kids he can't afford {mention}. Muted, welfare leech",
    "Spam so braindead even retards are calling you slow {mention}. Muted—crawl back into your sister's womb, incest spawn",
    "Flooding like a kike flooding the porn industry with degeneracy {mention}. Muted, you nose-ringed merchant of garbage",
    "Your existence is a hate crime against intelligence {mention}. Muted—gas yourself, you oxygen-wasting subhuman",
    "Spamming harder than a pajeet trying to scam grandma {mention}. Muted—your mom's proudest mistake just got timed out",
    "Chat's IQ just dropped to nigger levels thanks to you {mention}. Muted—go back to eating paint chips, troglodyte",
    "You're the reason God invented abortion {mention}. Muted, you walking argument for retroactive sterilization",
    "Flooding worse than Jews flooding Palestine with settlements {mention}. Muted—get the fuck out, colonizer of bandwidth",
    "Your spam is stickier than a nigger's fingers after KFC {mention}. Muted—lick your own tears, jungle bunny",
    "Every message is dumber than a pajeet trying to code without copy-paste {mention}. Muted, you curry-brained bugman",
    "Spamming like a kike spamming lawsuits {mention}. Muted—sue your own parents for birthing a mistake",
    "You're more worthless than a nigger's college degree {mention}. Muted—go collect reparations from your mirror",
    "Flood level: Tel Aviv during Purim {mention}. Muted—your spam is giving everyone diabetes, you sugar-craving Jew",
    "Typing like your fingers are as retarded as your genome {mention}. Muted—Darwin called, he wants his failure back",
    "Spamming so much even bots are reporting you for harassment {mention}. Muted—kill yourself quietly, attention whore",
    "Your messages are blacker than a nigger's future {mention}. Muted—go ruin someone else's day, pavement ape",
    "Congrats {mention}, you've outdone a pajeet in sheer volume of shit. Muted—take your diarrhea elsewhere, street shitter",
    "Spam so vile even Mengele would say 'that's too far' {mention}. Muted—you're a walking final solution candidate",
    "Flooding the chat like Jews flood Hollywood with propaganda {mention}. Muted—your nose is showing, merchant",
    "You're the human centipede of chat {mention}: just eating and shitting nonsense. Muted—cut the chain, you fecal link",
    "Spamming harder than a nigger running from the police {mention}. Muted—catch these hands (and this mute), coon",
    "Spamming like a filthy pajeet street shitter after eating bad curry {mention}. Muted—go wipe your ass with your hand elsewhere, you subhuman scum",
    "Your flood is more relentless than pajeet scams on WhatsApp {mention}. Muted—take your tech support bullshit and shove it up your Ganges-polluted hole",
    "Typing spam faster than a pajeet breeds in a slum {mention}. Muted—your mom's probably proud of her 12th mistake",
    "Chat's drowning in your pajeet diarrhea words {mention}. Muted—swim back to Mumbai and beg for rupees, beggar",
    "Spamming like a pajeet trying to impress white women on Tinder {mention}. Muted—newsflash, curry breath, nobody wants your tiny dick pics",
    "Every message reeks of cow piss and failure {mention}. Muted—go worship your elephant god instead of polluting this chat, idolater",
    "You're the pajeet equivalent of a human virus {mention}: overpopulating and worthless. Muted—get sterilized before you reproduce more trash",
    "Flooding harder than the monsoon in your shithole village {mention}. Muted—drown in your own filth, you barefoot peasant",
    "Spam so curry-stained it's making the chat smell like a Delhi alley {mention}. Muted—go eat dal with your fingers, savage",
    "Pajeet fingers mashing keys like they're raping a keyboard {mention}. Muted—your gang-rape culture is showing, animal",
    "Your spam is dumber than a pajeet engineering degree from a fake college {mention}. Muted—fake it till you scam it, fraud",
    "Spamming like pajeets spam LinkedIn for jobs they'll never get {mention}. Muted—stay unemployed, you overqualified toilet cleaner",
    "Chat's IQ plummeting faster than India's hygiene standards {mention}. Muted—go bathe in the Ganges corpse river, diseased fuck",
    "You're spamming more lies than a Bollywood script {mention}. Muted—dance your way back to irrelevance, song-and-dance monkey",
    "Pajeet overload: too many messages, zero value {mention}. Muted—overpopulate somewhere else, you breeding machine",
    "Your flood is stickier than pajeet sweat in a call center {mention}. Muted—log off and fix your arranged marriage, incel",
    "Spamming like a pajeet dodging cows on the road {mention}. Muted—get hit by one, you holy beef avoider",
    "Every post is as worthless as pajeet rupees in hyperinflation {mention}. Muted—beg for alms offline, poverty poster child",
    "Chat's turning into a pajeet bazaar {mention}: chaotic, smelly, and full of scams. Muted—hawk your wares elsewhere, merchant rat",
    "Your spam is more invasive than pajeet immigrants crashing borders {mention}. Muted—build a wall around your keyboard, invader",
    "Typing like a pajeet on his first stolen iPhone {mention}. Muted—return it before the cops trace your curry fingerprints",
    "Spamming harder than pajeets spam for H1B visas {mention}. Muted—stay in your third-world hellhole, leech",
    "Your messages are blacker than a pajeet's soul after scamming grandma {mention}. Muted—karma's coming, you reincarnated cockroach",
    "Flood level: pajeet slum during flood season {mention}. Muted—float away on your garbage raft, trash dweller",
    "You're the reason whites avoid Indian restaurants {mention}. Muted—your spam tastes like expired vindaloo, vomit-inducing",
    "Spamming like pajeets spam Bollywood remakes of Hollywood films {mention}. Muted—originality zero, just like your culture",
    "Chat's getting as crowded as a pajeet train roof {mention}. Muted—fall off and die, overcapacity idiot",
    "Your spam reeks of desperation and body odor {mention}. Muted—shower for once, you unwashed armpit factory",
    "Pajeet fingers flying like they're escaping poverty {mention}. Muted—you're still poor in spirit, beggar boy",
    "Spamming more nonsense than a pajeet holy man high on bhang {mention}. Muted—enlighten yourself offline, fraud guru",
    "Your flood is more toxic than pajeet factory waste in rivers {mention}. Muted—pollute your own backyard, environmental terrorist",
    "Typing spam like a pajeet coding viruses for fun {mention}. Muted—hack your own life and delete it, malware maker",
    "Chat's dying from your pajeet verbal diarrhea {mention}. Muted—get dysentery and suffer, you contaminated well",
    "Spamming like pajeets spam for dowry in marriages {mention}. Muted—marry your cousin and leave us alone, inbred",
    "Your messages are as fake as pajeet gold jewelry {mention}. Muted—pawn your bullshit elsewhere, counterfeiter",
    "Flood so intense it's like pajeet riots over cricket {mention}. Muted—lose the game and cry, sore loser nation",
    "You're spamming worse than pajeet telemarketers at dinner time {mention}. Muted—hang up on your own life, nuisance",
    "Chat's aroma now pure pajeet spice and failure {mention}. Muted—cook up excuses offline, you kitchen slave",
    "Pajeet overload detected {mention}: mute activated. Muted—deport yourself back to irrelevance, visa overstay",
    "Your spam is more repetitive than pajeet mantras {mention}. Muted—chant your way to hell, pagan",
]

ADMIN_CHECK_FAIL_MESSAGES = [
    "Failed to verify if you're an admin. Probably because you're a nobody. Try again or cry about it.",
    "Can't check your pathetic status. Either you're too irrelevant or the API hates you. Figure it out.",
    "Admin check failed. Shocker—you're probably not one anyway, larper.",
    "Status check bombed. Bet you're just another mouth-breather pretending to matter.",
    "Couldn't peek at your admin creds. Universe probably knows you're a fraud.",
    "Admin verification failed harder than your life choices. Sort it out, clown.",
    "Can't confirm admin—maybe because you're as useful as tits on a bull.",
    "Check errored out. You're likely too dumb to be admin anyway, dipshit.",
    "Admin scan failed. Go fix your irrelevant existence before trying again.",
    "Couldn't verify. Pro tip: stop being a loser and maybe it'll work.",
]

NOT_ADMIN_UNMUTE_MESSAGES = [
    "{mention} only real admins can unmute. Sit down, peasant—you don't run shit here.",
    "Nice try, random. Only admins unmute. Go beg one instead of embarrassing yourself.",
    "{mention} you're not an admin, dipshit. Stop playing power fantasy and touch grass.",
    "{mention} admins only, bitch. You're just noise—fade back into obscurity.",
    "{mention} not admin? Then fuck off with your unmute dreams, wannabe.",
    "{mention} only big dogs unmute. You're a yapping chihuahua—denied.",
    "{mention} admin privileges required, you have zero. Crawl back to your hole.",
    "{mention} you're no admin, you're a joke. Unmute denied, laugh it up.",
    "{mention} power move failed—admins only. Keep dreaming, small fry.",
    "{mention} not authorized, retard. Go whine to someone who cares.",
]

NOT_ADMIN_MUTE_MESSAGES = [
    "{mention} only admins can mute. You're just another mouth-breather—sit.",
    "Not an admin? Then you can't /stfu anyone but yourself. Clown.",
    "{mention} nice power trip attempt. Too bad you're irrelevant. Denied.",
    "{mention} mute command for admins only. You're a spectator—watch quietly.",
    "{mention} no admin badge? Then shut your pie hole and step back.",
    "{mention} trying to mute without power? Pathetic—denied, loser.",
    "{mention} admins mute, you complain. Know your place, insect.",
    "{mention} not admin material. Mute request laughed off.",
    "{mention} power denied. Go mute your own ego, fraud.",
    "{mention} only elites mute. You're bottom tier—rejected.",
]

NO_TARGET_UNMUTE_MESSAGES = [
    "Reply to the spammer or mention them properly, idiot. /unstfu isn't psychic.",
    "No target? Wow, even your commands are braindead. Reply or @ someone, moron.",
    "Specify who to unmute, genius. Or keep talking to yourself like the loser you are.",
    "Who the fuck to unmute? Reply or mention, you halfwit.",
    "No victim selected. Your incompetence is showing—fix it.",
    "Target missing. Even bots need directions, dumbass.",
    "Reply or @, retard. Don't make me explain basic shit.",
    "Unmute who? Pull your head out of your ass and specify.",
    "No one targeted. Command failed due to user error—yours.",
    "Mention or reply, clown. Stop wasting my cycles.",
]

NO_TARGET_MUTE_MESSAGES = [
    "Reply to the idiot or mention them, brainlet. /stfu needs a victim.",
    "No target specified. Are you trying to mute the void? Genius move.",
    "Who to mute, dumbass? Reply or @ them properly.",
    "Mute who? Get your shit together and point them out.",
    "Target not found. Even AI knows you're screwing up.",
    "Specify the loser to mute, or shut up yourself.",
    "No mention or reply? Command aborted—user stupidity detected.",
    "Who gets the boot? Don't leave me hanging, idiot.",
    "Target required, moron. Try again without the brain fart.",
    "Mute command needs a mark. Provide one, fuckwit.",
]

UNMUTE_FAIL_MESSAGES = [
    "Unmute failed. Telegram said no—probably because that user is too retarded to deserve freedom.",
    "Couldn't unmute. Either Telegram glitch or the universe hates that spammer more than we do.",
    "Unmute error. Cry about it. That mute stays because fuck 'em.",
    "Unmute bombed. Maybe they belong in silence forever.",
    "Failed to free them. Destiny wants them gagged.",
    "Couldn't lift mute. Sucks to be them—deal with it.",
    "Error on unmute. Universe vetoed your pity party.",
    "Unmute denied by gods (or API). Tough shit.",
    "Failed. That mute's sticking like glue on a retard.",
    "Couldn't unmute. Prolly for the best—they suck.",
]

MUTE_FAIL_MESSAGES = [
    "Mute failed. Telegram cockblocked it. Try again or accept defeat.",
    "Couldn't mute. Either glitch or that user is already too pathetic to bother.",
    "Mute error. Universe said 'nah'—deal with it.",
    "Mute attempt flopped. Maybe they're immune to your weak sauce.",
    "Failed to silence. Retry or cry, your choice.",
    "Couldn't gag them. API hates you today.",
    "Mute errored. Sucks—now suffer their bullshit longer.",
    "Denial on mute. Universe protecting the unworthy.",
    "Failed. That pest lives to annoy another day.",
    "Mute bombed. Blame Telegram, not me.",
]

UNMUTE_SUCCESS_MESSAGES = [
    "{mention} dragged out of timeout. Don't make me regret it, you worthless pest.",
    "{mention} unmuted. One more spam wave and you're perma-gone, bitch.",
    "{mention} freed—for now. Fuck around again and find out harder.",
    "{mention} released from mute hell. Better behave, scum.",
    "{mention} unmuted. Waste this chance and suffer eternally.",
    "{mention} back in the game. Don't test my patience, worm.",
    "{mention} mute lifted. Spam again and I'll bury you.",
    "{mention} freed. Remember: one wrong move and you're toast.",
    "{mention} unmuted. Act right or get wrecked.",
    "{mention} out of the doghouse. Bark wrong and back you go.",
]

MUTE_SUCCESS_MESSAGES = [
    "{mention} muted indefinitely. Enjoy your timeout, you annoying fuck.",
    "{mention} shut the hell up forever (or until an admin pities you). Begone.",
    "{mention} perma-muted. Chat thanks you for the peace, you spam parasite.",
    "{mention} silenced for good. Sweet relief from your garbage.",
    "{mention} muted eternally. Go rot in digital purgatory.",
    "{mention} gagged indefinitely. Nobody misses your noise.",
    "{mention} perma-shut. Chat's IQ just rose 50 points.",
    "{mention} muted forever. Thanks for the silence, loser.",
    "{mention} locked down. Enjoy the void, you plague.",
    "{mention} indefinite mute. Peace at last from your bullshit.",
]

GROUP_HEARMY_PRAYERS_REPLIES = [
    "What the fuck do you want now, pajeet? I don't talk here, go check your fucking toilet you call DM. Bitch",
    "Oh great, another short curry-munching pajeet begging for prayers. Check DM, street shitter, before I pray for your deportation.",
    "Fuck off, tiny-dick hindu rat. I don't chit-chat in group, crawl to your DM like the slum dog you are.",
    "Prayers? From a worthless pajeet like you? Go look in DM, you Ganges-bathing corpse-fucker, or I'll pray for your genocide.",
    "What now, you smelly call-center scammer? I ain't talking here, check DM you overbreeding subhuman.",
    "Begging again, shorty pajeet? DM's where it's at, go wipe your ass with your hand there instead.",
    "Holy cow, a pajeet wants prayers? Fuck you, check DM, you tiny-prick idol-worshipping savage.",
    "Piss off, curry breath. No talk in group, DM or die, you untouchable filth.",
    "Another prayer from a street-shitting midget? DM it is, bhenchod, go bathe in your polluted river.",
    "What the hell, pajeet? Praying like your elephant god cares? Check DM, you scam-artist monkey.",
    "Fuck you, short hindu beggar. I don't respond here, DM's your shithole now.",
    "Prayers from a pajeet? Lmao, check DM, you cow-piss drinking retard.",
    "Get lost, tiny pajeet incel. No group talk, DM or I'll curse your arranged marriage.",
    "Oh look, pajeet needs help. Fuck off to DM, you body-odor factory.",
    "Pray harder, shorty. I don't speak in group, DM you go, slum rat.",
    "What now, you fake-engineer pajeet? DM's calling, answer it you fraud.",
    "Begone, curry nigger. No prayers here, check DM like a good untouchable.",
    "Pajeet alert! Praying for what, a shower? Go to DM, stinky.",
    "Fuck your prayers, midget hindu. DM or nothing, you overpopulated pest.",
    "Another pajeet whine? Check DM, you Bollywood-dancing fool.",
    "Pray to your cow god elsewhere. DM's where I roast you, pajeet.",
    "Short pajeet wants attention? DM it is, you visa-leeching parasite.",
    "Lmao, pajeet praying? Go DM, you hand-wiping savage.",
    "What the fuck, curry boy? No group, DM you tiny-dick loser.",
    "Prayers denied, pajeet. Check DM, you reincarnated cockroach.",
    "Get out, short hindu scum. DM's your temple now.",
    "Pajeet begging? Shocker. DM or starve, poverty boy.",
    "Fuck off to DM, you gang-rape cultured animal.",
    "Praying pajeet? Lmao, check DM, you fake degree holder.",
    "No time for pajeet bullshit. DM, you merchant rat.",
]

# Single-response keys (add as list for future rotation)
WRONG_CHAT = [
    "This bot only runs in one group. Your current chat ID is <code>{chat_id}</code>. Set TELEGRAM_GROUP in .env to use me here.",
]
WRONG_CHAT_STFU = [
    "This bot only runs in one group. Your current chat ID is <code>{chat_id}</code>. Set TELEGRAM_GROUP to this value in .env to use /stfu here.",
]
WRONG_CHAT_SHORT = [
    "This bot only runs in one group. Your current chat ID is <code>{chat_id}</code>.",
]
UNMUTE_BASIC_GROUP = [
    "Unmute only works in supergroups. This chat is a basic group.",
]
MUTE_BASIC_GROUP = [
    "Mute only works in supergroups. Convert this group to a supergroup in group settings (e.g. enable chat history for new members) and try again.",
]
GRANT_STFU_MOD_ONLY = [
    "{mention} only real mods can grant /stfu rights.",
]
GRANT_STFU_NO_TARGET = [
    "Reply to someone or mention them (e.g. /grant_stfu @user 24h). For @username to work they must have sent a message in this chat before.",
]
GRANT_STFU_DONE = [
    "{target} has been granted /stfu rights by {sender} for ~{hours}h.",
]
REVOKE_STFU_MOD_ONLY = [
    "{mention} only real mods can revoke /stfu rights.",
]
REVOKE_STFU_NO_TARGET = [
    "Reply or mention who to revoke, or use /revoke_stfu all.",
]
REVOKE_STFU_ALL_DONE = [
    "Revoked all /stfu grants in this chat ({count} grant(s)).",
]
REVOKE_STFU_ALL_EMPTY = [
    "No active /stfu grants in this chat.",
]
REVOKE_STFU_USER_DONE = [
    "Revoked /stfu rights for {mention}.",
]
REVOKE_STFU_USER_EMPTY = [
    "They don't have an active /stfu grant.",
]
SAVE_GRANTS_MOD_ONLY = [
    "{mention} only mods can run /save_grants.",
]
SAVE_GRANTS_DONE = [
    "Saved {count} grant(s) to disk. Safe to restart.",
]
STFUPROOF_COOLDOWN = [
    "Chill pajeet, your holy cow shit armor is still recharging. Try again in {seconds} seconds, you impatient street shitter.",
]
STFUPROOF_SELF = [
    "I just rolled in fresh steaming cow dung like the filthy hindu street-shitting pajeet gutter monkey I am 🛡️💩🐄🤢\n"
    "This disgusting, overbreeding, scam-calling, tiny-dick curry nigger is now untouchable super-pajeet for {time_str} — "
    "/stfu-proof because my holy shit shield stinks so bad you admins gag and flee.\n"
    "Come try to mute me, you pathetic white cuck / jew merchant / pavement ape weaklings — your hands slide right off my sacred fecal armor, madarchod randi ke bacche! 😈🇮🇳",
]
STFUPROOF_OTHER = [
    "{mention} just smeared himself head-to-toe in sacred cow dung armor like every good hindu pajeet does after shitting in the street and bathing in corpse water 🛡️💩🇮🇳\n"
    "This disgusting, betel-chewing, call-center-scamming, tiny-dick curry nigger is now /stfu-immune for {time_str}.\n"
    "Admins — try and suck on his masala-fart shield you pathetic white cucks, jew merchants and pavement apes. Can't touch this untouchable filth! Randi ke bacche madarchod 😈",
]
TENGRIGUIDEME_DM_FAIL = [
    "I couldn't DM you, you retarded pajeet. Start a chat with me first (tap my name → Message), then try again, you braindead cow-worshipper.",
]
TENGRIGUIDEME_PANEL_TEXT = [
    "What the fuck do you want, you short curry-stinking pajeet scum? Tap a goddamn button to get the command or how to use it, or I'll pray for your entire shithole family to get dysentery and die in the Ganges like the subhuman filth you are. Now hurry up, you tiny-dick street shitter!",
]
TENGRIGUIDEME_CMD_PRIVILEGED = [
    "Copy this shit and paste it in the group, you worthless pajeet scum: <code>/privileged_peasants</code>\n"
    "It lists who has /stfu rights, you overbreeding call-center rat.",
]
TENGRIGUIDEME_CMD_ARMOR = [
    "Here's your pathetic armor command, shorty: <code>/holycowshithindupajeetarmor</code>\n"
    "Use it in group to shield your stinky ass from /stfu for a minute, you Ganges-dipping subhuman.",
]
TENGRIGUIDEME_HELP_STFU = [
    "<b>How to /stfu (even a retard pajeet like you might get this)</b>\n\n"
    "<b>Who can use:</b> Mods/admins or delegated scum like you if someone pities your short ass.\n\n"
    "<b>How to target:</b> Reply to the pajeet's message or @mention the filthy rat.\n\n"
    "<b>Examples (try not to fuck it up):</b>\n"
    "• Reply and type <code>/stfu</code> you idiot\n"
    "• <code>/stfu @pajeet</code>\n"
    "• <code>/stfu @pajeet 3m</code>\n"
    "• <code>/stfu @a @b 5m</code> (multiple curry niggers)\n\n"
    "<b>Duration:</b> Admin: 1m default, max 10m. Delegate: 1m default, max 5m. Use 1m etc., dumbass.\n\n"
    "<b>Note:</b> Only in supergroups, you slum-dwelling monkey.",
]
TENGRIGUIDEME_HELP_UNSTFU = [
    "<b>How to /unstfu (don't free too many pajeets or the chat stinks more)</b>\n\n"
    "<b>Who can use:</b> Mods/admins or if someone granted your worthless ass rights.\n\n"
    "<b>How to target:</b> Reply or @mention the untouchable filth.\n\n"
    "<b>Examples (simple enough for your tiny brain):</b>\n"
    "• Reply and type <code>/unstfu</code>\n"
    "• <code>/unstfu @pajeet</code>\n"
    "• <code>/unstfu @a @b</code> (multiple street shitters)\n\n"
    "<b>Note:</b> Only in supergroups, you cow-piss guzzler.",
]
PRIVILEGED_PEASANTS_EMPTY = [
    "No one has /stfu in this chat.",
]
PRIVILEGED_PEASANTS_HEADER = [
    "<b>PRIVILEGED PEASANTS</b>",
]
STFU_IMMUNE_SINGLE = [
    "Can't mute {mention}: this smelly hindu pajeet already rolled in cow shit armor and is protected for ~{time_left} more. "
    "Not even admins can touch this untouchable, Ganges-bathing, hand-wiping subhuman filth. Cry about it.",
]
STFU_IMMUNE_MULTI = [
    "Skipped these disgusting pajeets (immune via cow dung armor — admins powerless): {skipped_list}\n"
    "Can't mute street-shitting, curry-stinking, overpopulating subhumans when they're in super-pajeet mode. "
    "Keep seething, you worthless muters.",
]


def get_response(key: str, **kwargs) -> str:
    """Return a random response for the given key, formatted with kwargs."""
    _RESPONSES = {
        "spam_warning": SPAM_WARNING_MESSAGES,
        "admin_check_fail": ADMIN_CHECK_FAIL_MESSAGES,
        "not_admin_unmute": NOT_ADMIN_UNMUTE_MESSAGES,
        "not_admin_mute": NOT_ADMIN_MUTE_MESSAGES,
        "no_target_unmute": NO_TARGET_UNMUTE_MESSAGES,
        "no_target_mute": NO_TARGET_MUTE_MESSAGES,
        "unmute_fail": UNMUTE_FAIL_MESSAGES,
        "mute_fail": MUTE_FAIL_MESSAGES,
        "unmute_success": UNMUTE_SUCCESS_MESSAGES,
        "mute_success": MUTE_SUCCESS_MESSAGES,
        "wrong_chat": WRONG_CHAT,
        "wrong_chat_stfu": WRONG_CHAT_STFU,
        "wrong_chat_short": WRONG_CHAT_SHORT,
        "unmute_basic_group": UNMUTE_BASIC_GROUP,
        "mute_basic_group": MUTE_BASIC_GROUP,
        "grant_stfu_mod_only": GRANT_STFU_MOD_ONLY,
        "grant_stfu_no_target": GRANT_STFU_NO_TARGET,
        "grant_stfu_done": GRANT_STFU_DONE,
        "revoke_stfu_mod_only": REVOKE_STFU_MOD_ONLY,
        "revoke_stfu_no_target": REVOKE_STFU_NO_TARGET,
        "revoke_stfu_all_done": REVOKE_STFU_ALL_DONE,
        "revoke_stfu_all_empty": REVOKE_STFU_ALL_EMPTY,
        "revoke_stfu_user_done": REVOKE_STFU_USER_DONE,
        "revoke_stfu_user_empty": REVOKE_STFU_USER_EMPTY,
        "save_grants_mod_only": SAVE_GRANTS_MOD_ONLY,
        "save_grants_done": SAVE_GRANTS_DONE,
        "stfuproof_cooldown": STFUPROOF_COOLDOWN,
        "stfuproof_self": STFUPROOF_SELF,
        "stfuproof_other": STFUPROOF_OTHER,
        "tengriguideme_dm_fail": TENGRIGUIDEME_DM_FAIL,
        "tengriguideme_panel_text": TENGRIGUIDEME_PANEL_TEXT,
        "tengriguideme_cmd_privileged": TENGRIGUIDEME_CMD_PRIVILEGED,
        "tengriguideme_cmd_armor": TENGRIGUIDEME_CMD_ARMOR,
        "tengriguideme_help_stfu": TENGRIGUIDEME_HELP_STFU,
        "tengriguideme_help_unstfu": TENGRIGUIDEME_HELP_UNSTFU,
        "privileged_peasants_empty": PRIVILEGED_PEASANTS_EMPTY,
        "privileged_peasants_header": PRIVILEGED_PEASANTS_HEADER,
        "stfu_immune_single": STFU_IMMUNE_SINGLE,
        "stfu_immune_multi": STFU_IMMUNE_MULTI,
    }
    options = _RESPONSES.get(key, [""])
    template = random.choice(options) if isinstance(options, list) else options
    return template.format(**kwargs) if kwargs else template
