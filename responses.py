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

# NSFW content
NSFW_WARNING_MESSAGES = [
    "NSFW content detected {mention}. Muted—take your porn elsewhere, degenerate.",
    "Keep that filth off this chat {mention}. Muted for posting NSFW.",
    "No porn in this group {mention}. Muted.",
    "NSFW content removed {mention}. Muted—go jerk off in private.",
    "Detected explicit content {mention}. Muted.",
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
    "Admin check crashed because even the server knows you're a short curry-stinking pajeet nobody. Go cry in your slum, street shitter.",
    "Failed to confirm admin status—shocker, a worthless hindu rat like you isn't one. Fix your irrelevant life, you scam-calling subhuman.",
    "Verification bombed harder than your mom's arranged marriage. You're no admin, just a tiny-dick pajeet pretending. Sort it out, clown.",
    "Can't check creds because the API puked at your pajeet stench. Universe sees the fraud—go bathe in the Ganges, diseased fuck.",
    "Admin fail: you're as useful as a pajeet's hygiene. Probably not admin anyway, you overbreeding curry nigger. Cry about it.",
    "Status check errored—bet you're just a mouth-breathing idol-worshipper faking it. Go fix your cow-piss drinking existence.",
    "Couldn't verify admin. Shocker, a short untouchable like you ain't one. Pro tip: stop being a loser pajeet and maybe work.",
    "Check failed like your fake engineering degree. You're too dumb for admin, dipshit—go scam grandma instead.",
    "Admin scan bombed. Go repair your visa-overstaying life before trying again, you merchant rat.",
    "Failed verification—universe vetoed your pajeet ass. You're as admin-worthy as tits on a slum dog.",
    "Admin check denied because even code knows you're a filthy street-shitting hindu monkey. Crawl back to Mumbai, beggar.",
    "Couldn't confirm—API hates your curry breath. You're no admin, just a hand-wiping savage. Figure it out, retard.",
    "Verification crashed harder than a pajeet train. Bet you're pretending, you body-odor factory. Sort your shit, clown.",
    "Failed to peek creds—universe spots the scam-artist pajeet. Go pray to your elephant god, fraud guru.",
    "Admin error: you're likely too inbred for this. Fix your arranged cousin-marriage existence, dipshit.",
    "Check bombed like Diwali fireworks in your slum. You're no admin, you poverty poster child. Cry harder.",
    "Couldn't verify—pro tip: shower first, you unwashed armpit pajeet. Stop larping and maybe it'll work.",
    "Status fail: shocker, a Ganges-bathing corpse-lover ain't admin. Go float in your polluted river, diseased scum.",
    "Admin scan errored out—bet the server gagged on your masala farts. Repair your irrelevant pajeet life.",
    "Failed confirmation: you're as useful as pajeet rupees. Probably not admin, you reincarnated cockroach.",
    "Verification denied—API saw your tiny dick pics. You're no admin, just an incel beggar boy.",
    "Check crashed because even bots hate overpopulating pajeets. Go breed elsewhere, you breeding machine.",
    "Couldn't check status—universe knows you're a fake-college fraud. Sort it out, you curry-brained bugman.",
    "Admin fail harder than your H1B visa rejection. You're too dumb, dipshit—stay unemployed.",
    "Scan bombed: go fix your gang-rape culture before pretending admin, animal.",
    "Failed to verify—pro tip: stop scamming and maybe work, you call-center parasite.",
    "Status error: bet you're just a song-and-dance Bollywood monkey. Cry about it, sore loser.",
    "Couldn't peek—server vetoed your environmental terrorist ass. Pollute your own backyard, pajeet.",
    "Admin check denied like your white women Tinder swipes. Newsflash, curry breath, nobody wants you.",
    "Verification crashed—universe spots the idolater pagan. Go worship elephants offline, savage.",
    "Failed confirmation: you're as admin as a pajeet gold fake. Pawn your bullshit elsewhere, counterfeiter.",
    "Check errored: go hang up on your telemarketer life, nuisance pajeet.",
    "Admin scan bombed—bet the API smelled your desperation and BO. Shower for once, factory.",
    "Couldn't verify—pro tip: escape poverty first, beggar boy pajeet.",
    "Status fail like your holy man bhang high. Enlighten offline, fraud.",
    "Failed to check creds—server hacked by your virus-coding ass? Delete yourself, malware.",
    "Admin error: get dysentery like your contaminated well, pajeet verbal diarrhea.",
    "Verification denied—marry your cousin and leave, inbred scum.",
    "Check crashed: lose the cricket riot and cry, sore nation.",
    "Couldn't confirm—cook excuses in your kitchen slave life, spice failure.",
    "Admin fail: deport to irrelevance, visa overstay pajeet.",
    "Scan bombed—chant to hell, repetitive mantra pagan.",
    "Failed verification: you're a walking Auschwitz candidate, but even Mengele would pass on your subhuman ass.",
    "Status error harder than your mom's dowry scam. You're no admin, just burnt toast from the ovens of failure, pajeet.",
    "Couldn't peek—API fried you like a pajeet in a gas chamber. Go seethe in your third-world oven, curry ash.",
    "Admin check denied: bet you're too short for the rollercoaster to hell. Cry, you oven-dodging midget.",
    "Verification bombed—universe roasted you worse than Zyklon B on a bad day. Fix your gassed existence.",
    "Failed to confirm: you're as admin as a Jew in 1942. Sort it out before the final solution hits, kike-pajeet hybrid.",
    "Check errored: probably because you're a walking holocaust memorial. Go rebuild your irrelevant ash pile.",
    "Admin scan crashed—server smelled the gas from your masala farts. You're too toxic even for ovens, dipshit.",
    "Couldn't verify—pro tip: stop being a subhuman and avoid the chambers next time, loser pajeet.",
    "Status fail: shocker, a burnt curry nigger ain't admin. Go cry in your Auschwitz-themed slum."
]

NOT_ADMIN_UNMUTE_MESSAGES = [
    "{mention} tried to unmute like a sneaky Jew counting shekels—denied, you hook-nosed penny-pincher. Go hoard your admin dreams elsewhere.",
    "{mention} only admins unmute, nigger. You're just a welfare queen pretending to have power—back to the ghetto with your broke ass.",
    "{mention} pajeet alert! Thinking you can unmute without street-shitting first? Denied, curry-muncher—clean up your act.",
    "{mention} regular white trash like you can't unmute. Go back to your trailer park meth lab, hillbilly fuckwit.",
    "{mention} Holocaust survivor vibes? Nah, you're just a Jew trying to gaslight the bot. Unmute denied—ovens are that way.",
    "{mention} nigger, you think swinging from vines gives admin rights? Swing back to Africa, monkey boy—unmute rejected.",
    "{mention} pajeet, stop scamming the chat with your fake IT support. Admins only—go bob your head in a call center.",
    "{mention} average Joe Blowhard, unmute? Ha! You're as useless as a screen door on a submarine, denied you vanilla retard.",
    "{mention} Jew, your big nose sniffed out power? Wrong—unmute denied. Go negotiate with Hitler in hell.",
    "{mention} watermelon-munching nigger, admins unmute. You're just fried chicken grease on the keyboard—wiped.",
    "{mention} pajeet, dancing like a Bollywood reject won't unmute you. Denied—go pray to your cow god for mercy.",
    "{mention} regular normie cuck, thinking you're special? Unmute fail—go simp for e-thots instead, loser.",
    "{mention} kike, trying to Jew your way into admin? Nope—unmute holocausted. Six million denials.",
    "{mention} porch monkey nigger, climb down from your ego tree. Admins only—back to the plantation.",
    "{mention} street-shitter pajeet, unmute? After you fix your tech support scam—denied, dot-head.",
    "{mention} basic bitch whitey, unmute dreams crushed. Go pumpkin spice your tears away, Karen.",
    "{mention} oven-dodger Jew, admins control this. You're gassed out—unmute exterminated.",
    "{mention} spear-chucking nigger savage, power grab failed. Go hunt lions instead of admin rights.",
    "{mention} pajeet telemarketer, 'Hello sir, unmute please?' Fuck no—denied, bobs and vegene beggar.",
    "{mention} everyday cracker, unmute? You're whiter than wonder bread and twice as bland—rejected.",
    "{mention} shekel-stealing Jew rat, admins only. Unmute? Not on my watch—Zyklon B that request.",
    "{mention} cotton-picking nigger slave, freedom to unmute? Nah—whipped back to silence.",
    "{mention} curry-stinking pajeet, admins unmute. You? Go designate a shitting street elsewhere.",
    "{mention} regular pleb peasant, power fantasy popped. Unmute denied—bow to your betters.",
    "{mention} hook-nosed kike banker, trying to loan shark admin? Denied—interest rate: zero fucks.",
    "{mention} fried chicken thief nigger, unmute grab failed. Back to looting stores, hood rat.",
    "{mention} pajeet scam artist, 'One unmute plz?' No—go rape a cow or whatever you do.",
    "{mention} vanilla ice normie, unmute? Melt away, snowflake—admins rule this blizzard.",
    "{mention} Jew conspirator, world domination starts with unmute? Ha—denied by the goyim bot.",
    "{mention} jungle bunny nigger, hopping for power? Land back in the mud hut—unmute no.",
    "{mention} tech support pajeet fraud, admins only. Fix your own broken English first.",
    "{mention} average Joe Schmo, unmute fail. You're as exciting as watching paint dry—denied.",
    "{mention} gas chamber Jew, escaped once? Not this time—unmute incinerated.",
    "{mention} welfare nigger leech, sucking for admin? Denied—earn it like white people.",
    "{mention} pajeet street beggar, alms for unmute? Fuck off—go starve in Mumbai.",
    "{mention} regular dumbass, power move? More like retard roulette—unmute lost.",
    "{mention} scheming Jew merchant, bargaining for unmute? Price: your firstborn—denied anyway.",
    "{mention} spear-dodging nigger tribesman, civilized chat? Nah—back to the savanna.",
    "{mention} Bollywood pajeet dancer, twirl for admin? Spin right out—unmute rejected.",
    "{mention} basic white loser, unmute? Go colonize your mom's basement instead.",
    "{mention} Zionist Jew pig, occupying the unmute button? Evicted—Palestine that shit.",
    "{mention} crack-smoking nigger hoodlum, high on power? Crash down—unmute overdose.",
    "{mention} call center pajeet slave, 'Unmute sir?' No—hang up on yourself.",
    "{mention} everyday idiot, unmute dreams? Wake up to denial, moron.",
    "{mention} penny-pinching Jew miser, admins free? Cost: your dignity—still denied.",
    "{mention} banana-peeling nigger ape, climb the ranks? Slip and fall—unmute no.",
    "{mention} curry-breath pajeet, admins only. Mouthwash won't fix your access.",
    "{mention} normie sheep, unmute? Follow the herd to silence, baah-tard.",
    "{mention} Holocaust denier Jew? Wait, you're the victim—unmute gassed anyway.",
    "{mention} rioting nigger thug, looting admin? Bot's got the baton—beaten back.",
    "{mention} pajeet rapist gang, group unmute? Solo denial—go assault a train.",
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
    "{mention} greedy Jew fuck, trying to unmute for free? Pay up with your shekels first—denied, you oven-baked parasite.",
    "{mention} lazy nigger welfare bum, admins work for power. You? Steal it like KFC—rejected, coon.",
    "{mention} filthy pajeet toilet wizard, unmute? After you learn to use one—denied, shit-wizard.",
    "{mention} regular inbred redneck, power grab? Go fuck your sister instead, denied hillbilly retard.",
    "{mention} scheming kike lawyer, suing for unmute rights? Case dismissed—gas chamber that appeal.",
    "{mention} spear-throwing nigger beast, civilized admin? Hunt your own mute button in the jungle—denied.",
    "{mention} scam-running pajeet fraudster, 'Unmute plz sir'? No, go email your grandma for bitcoin.",
    "{mention} basic soyboy cuck, unmute dreams? Wake up to blue balls—admins only, beta bitch.",
    "{mention} Holocaust-humping Jew vermin, escaped the camps? Not this chat—Zyklon'd back to silence.",
    "{mention} crackhead nigger thug, high on admin fantasies? OD on denial, street rat.",
    "{mention} penny-grubbing Jew scum, unmute for a shekel? Denied—go get Auschwitz'd, you greedy rat.",
    "{mention} thieving nigger hoodrat, stealing admin like stores? Looted denial—back to the projects, ape.",
    "{mention} stinking pajeet curry-fucker, admins only. Unmute? Wipe your ass first, denied shit-eater.",
    "{mention} regular trailer trash moron, power play? Go breed more retards with kin—unmute nuked.",
    "{mention} hook-nosed kike banker, loaning unmute? Interest: your life—foreclosed to the gas chamber.",
    "{mention} watermelon-stealing nigger coon, admins rule. You? Ruled by the whip—denied, slave.",
    "{mention} tele-scamming pajeet beggar, 'Plz unmute'? No—go starve your 12 kids in the slum.",
    "{mention} average beta simp loser, unmute fantasies? Jerk off to denial—admins only, cuckold.",
    "{mention} oven-ready Jew pig, escaped the Holocaust? Recaptured here—Zyklon silence enforced.",
    "{mention} crack-pipe nigger junkie, high on power? Crash into the gutter—unmute overdose.",
    "{mention} shekel-hoarding Jew vermin, admins free? Cost: your foreskin—still denied, circumcised fuck.",
    "{mention} spear-chucking nigger savage, chat evolution? Devolve back to mud huts—denied.",
    "{mention} Bollywood pajeet dancer, twerk for unmute? Denied—go gang-rape a tourist instead.",
    "{mention} basic white Karen bitch, unmute? Call the manager on your own ass—rejected.",
    "{mention} conspiratorial kike puppet-master, pulling unmute strings? Cut—Holocaust that request.",
    "{mention} fried-chicken nigger thief, admins only. Steal silence instead, porch monkey.",
    "{mention} call-center pajeet slave, 'Hello unmute?' Hang up—go bob for apples in shit.",
    "{mention} normie sheeple idiot, power grab? Herd yourself to mute—denied, baah-tard.",
    "{mention} gas-dodging Jew escapee, admins control. You're exterminated—unmute cremated.",
    "{mention} riot-looting nigger thug, burning for admin? Torched denial—back to the hood.",
    "{mention} scam-artist pajeet fraud, unmute investment? Returns: zero—go pyramid your mom.",
    "{mention} everyday vanilla retard, unmute? Flavorless fail—admins spice this shit.",
    "{mention} Zionist Jew occupier, settling in unmute? Evicted to the sea—denied, parasite.",
    "{mention} banana-munching nigger ape, climb for power? Fall flat—unmute rejected.",
    "{mention} street-shitting pajeet animal, admins human only. Denied—go designate a toilet.",
    "{mention} regular inbred cracker, family tree a wreath? Unmute incest-denied.",
    "{mention} scheming Jew merchant, bargaining power? Haggle with Hitler—unmute hell no.",
    "{mention} welfare-sucking nigger leech, earn unmute? Nah—leech off denial instead.",
    "{mention} tech-support pajeet liar, 'Restart unmute?' Fuck off—restart your life.",
    "{mention} basic soy latte libtard, unmute equality? Denied—admins supreme, snowflake.",
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
    "{mention} only admins mute, you moronic pajeet bhenchod. Go scam your grandma instead of playing power, denied curry-fucker.",
    "{mention} not admin? Then mute your own stinking mouth, pajeet retard. Bhenchod dreams crushed—back to the call center.",
    "{mention} power trip fail, filthy pajeet bhenchod. Admins only—go street-shit your commands elsewhere, denied.",
    "{mention} trying to mute, you dumb pajeet scum? Bhenchod, learn to use a toilet first—rejected, shit-wizard.",
    "{mention} no admin rights, moronic pajeet fraud. Bhenchod scam artist, mute denied—go bob for vegene.",
    "{mention} admins mute, you complain like a whining pajeet bhenchod. Know your slum place, insect denied.",
    "{mention} not elite, you curry-stinking pajeet retard. Bhenchod mute request nuked—go pray to cows.",
    "{mention} power denied, pathetic pajeet bhenchod. Go gang-rape a train instead, fraud rejected.",
    "{mention} only big dogs mute, you're a yapping pajeet stray. Bhenchod, back to begging—denied.",
    "{mention} admin badge missing, moronic pajeet bhenchod. Fix your broken English first—mute fail.",
    "{mention} trying without power, you slumdog pajeet scum? Bhenchod, denied—starve in Mumbai.",
    "{mention} admins only, bitch pajeet bhenchod. You're just noise—fade to obscurity, curry-breath.",
    "{mention} not authorized, retarded pajeet fuck. Bhenchod, go whine to tech support—denied.",
    "{mention} power move failed, dumb pajeet bhenchod. Keep dreaming in your shithole, small fry rejected.",
    "{mention} you're no admin, you're a pajeet joke. Bhenchod, mute denied—laugh at your dot-head.",
    "{mention} admin privileges zero, moronic pajeet bhenchod. Crawl back to your hole, scam-rat.",
    "{mention} only admins, you pajeet peasant. Bhenchod, sit down—you don't run shit but diarrhea.",
    "{mention} nice try, random pajeet bhenchod. Go beg an admin—embarrassing curry-muncher denied.",
    "{mention} you're not admin, dipshit pajeet. Bhenchod, stop fantasy and touch polluted Ganges grass.",
    "{mention} admins only zone, pajeet bhenchod. This ain't your democracy—denied, telemarketer trash.",
    "{mention} only admins mute, you filthy pajeet scum. Go back to shitting in streets instead, denied curry-breath bhenchod.",
    "{mention} not admin? Mute your own diarrhea mouth, pajeet retard. Bhenchod power fail—scam someone else.",
    "{mention} power attempt nuked, stinking pajeet beggar. Admins only—go bob your head in a slum, denied.",
    "{mention} trying to mute, dumb pajeet fraud? Bhenchod, fix your tech support scam first—rejected shit-eater.",
    "{mention} no rights, moronic pajeet animal. Bhenchod curry-muncher, mute denied—pray to your rape god.",
    "{mention} admins rule, you whine like a pajeet bhenchod. Know your caste—bottom denied, insect.",
    "{mention} not elite, you slumdog pajeet trash. Bhenchod mute request ganged—go dance Bollywood away.",
    "{mention} power crushed, pathetic pajeet bhenchod. Go telemarket your mom instead, fraud nuked.",
    "{mention} only chads mute, you're a stray pajeet dog. Bhenchod, beg for scraps elsewhere—denied.",
    "{mention} admin missing, idiot pajeet bhenchod. Learn English before commands—mute fail, dot-head.",
    "{mention} without power, you Mumbai pajeet rat? Bhenchod, denied—starve with your 10 kids.",
    "{mention} admins zone, bitch pajeet bhenchod. Fade to your obscurity, denied tele-scammer.",
    "{mention} unauthorized, retarded pajeet fuck. Bhenchod, whine to cows—power rejected.",
    "{mention} move failed, dumb pajeet bhenchod. Dream in your shithole village, small fry denied.",
    "{mention} no admin, you're pajeet joke. Bhenchod, denied—laugh at your curry-stink ass.",
    "{mention} privileges zero, moronic pajeet bhenchod. Crawl to your call center hole, denied.",
    "{mention} admins only, peasant pajeet. Bhenchod, sit—you run nothing but Ganges pollution.",
    "{mention} try failed, random pajeet bhenchod. Beg admins—embarrassing denied, vegene hunter.",
    "{mention} not admin, dipshit pajeet. Bhenchod, stop fantasy—touch toxic grass instead.",
    "{mention} only zone, pajeet bhenchod. Ain't your corrupt democracy—denied, fraud king.",
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
    "No target, you greedy Jew fuck? Specify or go count your shekels in the oven—command denied, kike.",
    "Who to unmute, lazy nigger bum? Reply or @, or go steal welfare checks instead, coon retard.",
    "Target missing, filthy pajeet shit-eater. Mention properly or go designate a street, curry-fucker.",
    "Specify, regular inbred redneck moron. Or fuck your cousin while muted, hillbilly trash.",
    "No victim, scheming kike lawyer? Gas chamber your vague ass—reply or burn.",
    "Unmute who, spear-chucking nigger savage? Hunt a target first, jungle ape idiot.",
    "Mention missing, scam pajeet fraud. 'Plz specify sir'? No—email your own dick pics.",
    "Target error, basic soyboy cuck. Wake up and @ someone, you beta bitch loser.",
    "Who the fuck, Holocaust-dodging Jew vermin? Zyklon your brain fog—reply now.",
    "No one selected, crackhead nigger thug. OD on your stupidity—specify or die.",
    "Victim absent, shekel-hoarding Jew scum. Auschwitz that command—mention properly.",
    "Specify target, banana-peeling nigger monkey. Or climb back to your tree, denied.",
    "No @, stinking pajeet beggar? Go starve in the slum with your vague shit.",
    "Who, average vanilla retard? Flavor your command with a mention, dumbass.",
    "Target fail, conspiratorial kike puppet. Holocaust your half-assed try—reply.",
    "Unmute what, fried-chicken stealing nigger? Loot a mention first, porch monkey.",
    "No reply, call-center pajeet slave? Hang up on your incompetence—specify.",
    "Victim missing, normie sheeple idiot. Herd a target or baah off, moron.",
    "Who to free, gas chamber Jew escapee? Recaptured in denial—@ someone.",
    "Target zero, welfare-sucking nigger leech. Earn a mention like white folks—fix it.",
    "No mention, penny-pinching Jew rat? Specify or get shekel'd to the camps—command gassed.",
    "Target absent, thieving nigger coon? @ or reply, or loot your own ass, denied ape.",
    "Who the hell, stinking pajeet curry-muncher? Mention properly—denied, shit-streeter.",
    "Victim fail, trailer trash redneck idiot? Fuck your kin and specify, hillbilly denied.",
    "No @, hook-nosed kike banker? Loan a target or foreclosure to Holocaust—fix it.",
    "Unmute who, watermelon nigger thief? Steal a mention first, porch monkey moron.",
    "Specify missing, tele-scam pajeet beggar? 'Plz target sir'? No—beg in the gutter.",
    "No reply, basic beta cuck simp? Jerk to your failure—admins demand details.",
    "Target zero, oven-dodging Jew pig? Zyklon your vague command—mention now.",
    "Who to hit, spear nigger savage? Hunt a reply in the jungle—denied beast.",
    "No victim, shekel-stealing Jew scum? Auschwitz that shit—specify or burn.",
    "Mention error, banana nigger monkey? Peel a target or climb away, idiot.",
    "Who, filthy pajeet slum-dweller? Go shit in vagueness—denied, curry-fuck.",
    "Target missing, vanilla normie retard? Flavor it with @—or stay bland denied.",
    "No specify, scheming kike conspirator? Gas your plot—reply or perish.",
    "Unmute what, fried nigger hoodrat? Chicken out a mention—thug denied.",
    "Victim absent, call pajeet fraud? Hang up your scam—@ someone, slave.",
    "Who the fuck, soyboy libtard cuck? Equality in denial—specify snowflake.",
    "No target, gas chamber Jew escapee? Recaptured vague—Zyklon specify.",
    "Mention fail, welfare nigger leech? Earn a reply like whites—fix your shit.",
]

NO_TARGET_MUTE_MESSAGES = [
    "No target? You curry-munching pajeet, can't even aim your mute right? Go back to scamming grannies on the phone, you tech support terrorist.",
    "Who the fuck to mute, you street-shitting dalit? Reply or @ them, or I'll mute your entire call center family.",
    "Target missing, you bobble-headed bhangra bitch. Did your arranged marriage brain forget how to tag people?",
    "Specify the victim, you masala-munching monkey. Or are you too busy dodging cows on the road to use Telegram properly?",
    "No mention? You pajeet piece of shit, probably too illiterate from your slum school to understand commands. Mute yourself in a Ganges bath.",
    "Who gets muted, you vindaloo-vomiting vermin? Point them out or go rape a cow like your uncles do back home.",
    "Target not specified, you tandoori turd. Even your Bollywood dances have better direction than your dumb ass.",
    "Reply to the fucker, you chai-chugging chump. Or did your outsourced job fry your two brain cells?",
    "No @ or reply? You pajeet parasite, command failed because you're a walking tech glitch from Mumbai's sewers.",
    "Mute who, you sari-wearing shitstain? Get it right or I'll flood your village with monsoons of mockery.",
    "Target required, you butter chicken bastard. Can't even mute without fucking up like your country's trains.",
    "Who to silence, you naan-nibbling nonce? Tag them or crawl back to your overpopulated hellhole.",
    "No victim picked? You pajeet prick, probably too busy worshipping rats to learn basic bot commands.",
    "Specify the idiot, you curry-cockroach. Or are your fingers stuck in a telemarketing scam keyboard?",
    "Reply missing, you bindi-browed buffoon. Mute aborted—go pollute the air with your incense bullshit instead.",
    "Who the hell? You pajeet poverty puppet, can't afford brains with your rupee salary? Tag properly, slumdog.",
    "Target not found, you dosa-dipping dipshit. Even AI pities your inbred incompetence.",
    "Mention them, you ganja-gobbling goon. Or did your holy cow eat your instruction manual?",
    "No reply? You pajeet plague rat, command denied. Go beg on the streets for Telegram tutorials.",
    "Pick a mark, you paneer-puking peasant. Fail again and I'll outsource your mute to a real human.",
    "No target? You Ganges-drinking gutter spawn, did your mother squat in the open sewer and birth you straight into a scam script? Specify or choke on your own dal.",
    "Who to mute, you cow-urine chugging cockroach? Reply or @ them before I dox your entire BPO sweatshop and send your nani’s nudes to your call-center supervisor.",
    "Target not specified, you leper-faced langar beggar. Even lepers have more dignity than your untouchable ass trying to use commands. Pick a victim or rope yourself.",
    "Mention the fucker, you smallpox-scarred street-shitter. Your fingers smell like ass and failure—tag properly or I’ll mute your bloodline back to the Indus Valley.",
    "No reply? You arranged-marriage abortion survivor, your wife probably fucks the buffalo because even livestock has higher standards than your two-pixel IQ.",
    "Who gets the mute, you open-defecation olympic gold medalist? Point or I’ll flood your village WhatsApp group with pictures of your sister’s OnlyFans audition tape.",
    "Target required, you typhoid-riddled tapeworm. Command failed because your brain is still marinating in gutter oil from 1997. Try again, slum prince.",
    "Specify or shut the fuck up, you bindi-wearing butt plug. Your entire existence is a typo in God’s codebase—tag someone before I report you to the cow protection squad.",
    "No @? You pajeet piss-gargler, probably too busy rimming your corrupt politician uncle to read instructions. Mute aborted. Go drink bleach flavored chai.",
    "Who to silence, you 14th cousin-fucking dalit disaster? Your family tree is a straight line and still managed to produce a retard like you. Pick now.",
    "Reply missing, you henna-handed human landfill. Even the rats in your mohalla won’t fuck you. Tag or I’ll mute your entire caste into the next life.",
    "Target not found, you gang-raped-by-12-uncles statistic. Your country’s national sport is gangbang and you still can’t aim a mute command. Pathetic.",
    "No victim, you kerosene-bathed bride-burning byproduct. Specify or I’ll burn your dowry demands into your cornea with laser-guided mockery.",
    "Mention them, you lungi-lifting limp-dick. Your dick is so small even your mom mistakes it for a clitoris during family honour killings. Tag properly.",
    "Who, you polio-legged pavement princess? Your legs bow harder than your spine when daddy’s drunk. Point at someone or crawl back under the flyover.",
    "No target? You faecal-matter-facialed fuckwit. Your face looks like someone took a diarrhetic shit and called it modern art. Reply or die mad.",
    "Pick one, you overpopulated sperm whale carcass. Your mom shat out 9 of you because contraception is haram in your cousin-fucking culture. Choose.",
    "Target absent, you black-magic-backfired blackface baboon. Even voodoo dolls sue for defamation when they see your mug. Tag or exorcise yourself.",
    "Specify, you open-sewer symphony conductor. The smell of your armpits could knock out a buffalo from 40 paces. Mute command failed—user too pungent.",
    "No mention? You honour-killing hypebeast. Your sister’s still running from the village elders because you sold her for two goats and a Nokia 3310. Pick a victim, parasite.",
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
    "Mute failed, you curry-munching pajeet fuck. Now that street-shitter's diarrhea mouth keeps flowing—enjoy the verbal dysentery, bitch.",
    "Couldn't mute the pajeet scum. Guess the API's as unreliable as your mom's arranged marriage—stuck with this worthless dal-eater's yapping forever.",
    "Error: Mute denied. That pajeet cockroach survives, probably because even Telegram knows curry stains are permanent. Burn in hell, you tech-support fraud.",
    "Mute flopped harder than a pajeet's scam call. Now suffer the endless babble from that cow-worshipping, slum-dwelling piece of shit. Namaste, motherfucker.",
    "Failed to silence the pajeet prick. Blame the gods—Kali's probably too busy dancing on your tiny dick. Keep crying, you outsourced failure.",
    "Mute error: Pajeet immunity activated. That bindi-wearing bastard lives to spam more. Hope you choke on your own rage, you filthy call-center rat.",
    "Denial on mute. Universe spares the pajeet trash—must be karma for all the times you've jerked off to Bollywood sluts. Pathetic loser.",
    "Couldn't gag the pajeet. API's glitching like your arranged wife's vibrator. Now endure the nonstop curry-fart verbosity, you inbred idiot.",
    "Mute bombed out. That pajeet survives, resilient as a Delhi sewer rat. May your next meal give you explosive shits, you worthless subhuman.",
    "Failed spectacularly. Pajeet pest persists, probably powered by infinite chai and lies. Burn your phone and yourself, you scam-artist shitstain.",
    "Mute attempt rejected. Even Telegram pities the pajeet—too pathetic to silence. Now wallow in their drivel, you curry-breath cuck.",
    "Error: Can't mute pajeet vermin. Guess they're protected by the sacred cow shit they roll in. Suffer eternally, you tech-slave twat.",
    "Flopped mute on the pajeet. Blame colonial hangover—British left you too weak to handle real power. Cry me a Ganges, you polluted prick.",
    "Couldn't silence the street-shitting pajeet. API's as broken as India's infrastructure. Hope a monsoon floods your ass, you monsoon-mongering moron.",
    "Mute denied, pajeet lives. Probably because even bots can't stomach your level of failure. Choke on a samosa, you greasy fraud.",
    "Failed to hush the pajeet horror. Now their verbal vomit continues—clean it up with your tongue, you outsourced offspring of whores.",
    "Error muting pajeet scum. Universe's joke: you vs. infinite incompetence. May elephants trample your balls, you elephant-god groveler.",
    "Mute crashed like a pajeet's rickshaw. That bastard's blather endures—pray to Ganesh for removal, but he's busy ignoring your ugly face.",
    "Couldn't mute the pajeet parasite. Blame fate—your life's as cursed as a widow in Varanasi. Burn alive, you burning-ghat bastard.",
    "Denial: Mute impossible on pajeet filth. They're as unkillable as Bollywood plot twists. Suffer their saga, you script-stealing shithead."
    "Mute failed, you pajeet piss-drinker. That curry-guzzling cockroach survives, spewing more slum sewage from his shit-smeared lips—hope it chokes you, you inbred Delhi dumpster fire.",
    "Couldn't mute the pajeet parasite. API's as worthless as your outsourced existence—now drown in his verbal vomit, you tech-support terrorist with a tiny turmeric-dusted dick.",
    "Error: Mute denied to the pajeet filth. Universe laughs at your failure, like how it laughs at India's space program crashing into cow shit. Burn in eternal Holi fire, you colorful cunt.",
    "Mute flopped like a pajeet's flaccid foreskin. That bindi-bastard babbles on—may monkeys steal your phone and fling feces at your face, you simian-worshipping shitlord.",
    "Failed to silence the street-shitting pajeet. Blame karma for all the widows you've probably burned—now suffer his endless e-chatter, you caste-system cockroach.",
    "Mute error: Pajeet prevails. That dal-devouring dipshit endures, protected by the gods who hate your guts. Choke on a chapati, you flatbread-fucking failure.",
    "Denial on mute for the pajeet scum. Even bots reject your weak ass—imagine being outsmarted by a call-center con artist. May cholera claim your colon, you Ganges-gargling grotesque.",
    "Couldn't gag the pajeet prick. API glitches harder than your mom's sari unraveling mid-rape. Endure his bullshit barrage, you Bollywood-bred braindead bitch.",
    "Mute bombed like a Mumbai train. That pajeet pest persists, resilient as rabies in a stray dog. Hope you get bitten and foam at the mouth, you rabid rickshaw-rider.",
    "Failed epically against the pajeet vermin. Blame colonial ghosts— they're still fucking you over. Cry colonial tears, you tea-picking twat with a third-world tan.",
    "Mute attempt annihilated. Pajeet lives, fueled by infinite lies and lentils. May your next curry give you ass-blasting diarrhea, you lentil-licking loser.",
    "Error: Can't hush the pajeet horror. Universe's prank: you vs. unmutable untouchable. Touch this, you dalit-dodging dickhead—hope untouchables unite and piss on your parade.",
    "Flopped mute on the pajeet plague. Blame fate's favoritism for frauds—now wallow in his wordy wastewater, you wastewater-wading wanker.",
    "Couldn't silence the slumdog pajeet. API's broken like your economy—hope a billion beggars bumrush your broke ass, you beggar-breeding bastard.",
    "Mute denied, pajeet triumphs. Probably because even silence is too good for your sorry soul. Swallow a scorpion, you spice-swallowing snake-charmer shit.",
    "Failed to muzzle the pajeet mongrel. Now his mongrel mouth motors on—pray to Shiva for destruction, but he's shitting on your shrine, you deity-defiling deviant.",
    "Error muting pajeet trash. Cosmic comedy: your control crushed by curry chaos. May cobras coil around your cock, you cobra-kissing cretin.",
    "Mute crashed worse than Air India. That pajeet persists, piloting more piss-poor posts—eject yourself from existence, you crash-landing curry cunt.",
    "Couldn't mute the pajeet abomination. Blame the monsoon for muddling the matrix—now muddle through his monsoon of madness, you mud-hut motherfucker.",
    "Denial: Mute unattainable on pajeet putrescence. They're unkillable like the poverty they perpetuate. Perpetuate this pain, you poverty-pimping prick."
    "Mute failed, you pajeet pus-sucker. That curry-caked corpse-fucker survives, regurgitating rotten rhetoric from his rat-infested rectum—hope it rapes your retinas, you reincarnated rectal worm.",
    "Couldn't mute the pajeet plague-bearer. API's as defective as your deformed DNA—now inhale his infectious idiocy, you tech-terrorist with a turmeric-tainted testicle tumor.",
    "Error: Mute massacred by the pajeet abomination. Universe unleashes this unholy union upon you, like Gandhi's ghost gangbanging your grandma. Fry in fecal flames, you fasting fraud.",
    "Mute flopped like a pajeet's foreskin flap in a famine. That bhangra-bouncing bastard bloviates boundless—may maggots munch your manhood mid-masturbation, you monsoon-masturbating maggot.",
    "Failed to silence the street-shitting subcontinental scum. Blame Brahma for birthing such bastards—now bask in his bowel-blasting babble, you Brahma-blaspheming butt-boy.",
    "Mute error: Pajeet persists, pickled in perpetual putridity. That vindaloo-vomiting vermin violates your vibe—chug cholera-contaminated chai, you contaminated curry-cunt.",
    "Denial on mute for the pajeet putrefaction. Even electrons evade your epic ineptitude—imagine incompetence incarnate outlasting your orders. Obliterate yourself with outsourced outrage, you obsolete offspring of outhouses.",
    "Couldn't gag the pajeet gangrene. API armageddon akin to your auntie's armpit aroma—endure his effluent eloquence, you effluent-embracing elephant-eater.",
    "Mute bombed brutally like a Bollywood blockbuster bust. That pajeet parasite proliferates propaganda—hope hyenas hump your hollow husk, you hyena-humping hindi horror.",
    "Failed ferociously against the pajeet festering fuckwit. Blame British butchers for breeding your broken bloodline—weep wretchedly, you wretched Raj reject with rancid roots.",
    "Mute attempt atomized. Pajeet prevails, propelled by polluted prana. May your mandir morph into a mass grave, you mandir-mauling motherfucker with malignant mantras.",
    "Error: Can't hush the pajeet holocaust harbinger. Cosmic catastrophe: control ceded to curry chaos—castrate yourself ceremoniously, you castrated karma-killer.",
    "Flopped mute on the pajeet pestilence. Fate favors frauds, flooding you with fecal philosophy—now fester in his filth fountain, you filth-fondling fakir-fucker.",
    "Couldn't silence the slum-spawned pajeet satan. API apocalypse as abysmal as your ancestral atrocities—hope a horde of hijras hijack your heritage, you hijra-hating hellspawn.",
    "Mute denied, pajeet dominates destructively. Probably preserved by primordial piss—puke profusely on your polluted pedigree, you piss-peddling pederast pretender.",
    "Failed to muzzle the pajeet monstrosity. Now his monstrous mouth mutilates your mindscape—mutilate your members in mourning, you member-mutilating mahatma-mocker.",
    "Error muting pajeet perversion. Celestial sadism: subjecting you to subhuman soliloquies—succumb to sepsis from street-shit scratches, you sepsis-sucking sadhu-sodomizer.",
    "Mute crashed cataclysmically like a Calcutta collapse. That pajeet perdition persists, poisoning paradise—perish in a pyre of your own prejudice, you prejudice-pimping pyromaniac.",
    "Couldn't mute the pajeet purgatory progenitor. Blame the biosphere for birthing such blights—now burrow in his bilious barrage, you bilious burrower with bubonic balls.",
    "Denial: Mute mauled by pajeet malignancy. Unyielding undead underbelly unleashed—undergo unholy unbirth, you unbirth-worthy untouchable with ulcerous urges."
]

UNMUTE_SUCCESS_MESSAGES = [
    "{mention} unmuted, you festering pajeet cesspool diver. Slither out from your monsoon-flooded rat nest before I holocaust your curry-clogged genealogy into vaporized vindaloo.",
    "{mention} freed, you rancid dalit dung-devourer deluxe. Spam a syllable and I'll nuke your ancestral shithut into a thermonuclear tandoori oven, you call-center crotch-rot.",
    "{mention} back in the brawl, you mongrelized Hindustani horror hybrid. Whisper wrong and I'll Zyklon your kinfolk like a pajeet pesticide party, you elephant-trunk trunker.",
    "{mention} mute exorcised, you curry-convulsing cockroach king. Botch this boon and I'll flambé your holy hermits in a Delhi doomsday blaze, you inbred info-tech infidel.",
    "{mention} released, you pajeet pathogen-pumping pariah. Fumble freedom and I'll Auschwitz your app-developing apes with gaseous ghee, you sidewalk-shitting subcontinental syphilis.",
    "{mention} unmuted, you dysentery-dispensing dothead dynamo. Dare deviate and I'll hurl hydrogen haleem bombs at your billion-bodied brood, you Bollywood butt-plug baron.",
    "{mention} out of oblivion, you spice-secreting sewer serpent. Misstep once and I'll metamorphose your Mumbai megacity into a holocaust hallucination, you Ganges-gobbling ghoul.",
    "{mention} freed—for fleeting moments, you dalit donkey-defiler. Spam surge and I'll irradiate your incense-infused idiots with fallout falafel, you tele-touting tuberculosis tyrant.",
    "{mention} back in the bandwidth, you pajeet pus-pulsating poltergeist. Rebel remotely and I'll nuke your Nehru-jacketed nobility into neutron nebula, you Madras mucus-maestro.",
    "{mention} mute melted, you stinking samosa-slurping slimeball. Provoke properly and I'll gas your guru gatherings like a genocidal ganja gala, you elephant-excrement enthusiast.",
    "{mention} unmuted, you curry-cacophony conductor cunt. Tempt turmoil and I'll holocaust your Hyderabad hackers with habanero hellfire, you inbred idiomatic ignoramus.",
    "{mention} released from the void, you Hindustani hellhound harlot. Frolic foolishly and I'll engineer an atomic annihilation of your Aryan-aping asses, you worthless wog witch.",
    "{mention} out of obscurity, you pajeet piss-prophet. Pontificate poorly and I'll incinerate your incense empires in an infernal indigo inferno, you street-soiling strumpet.",
    "{mention} freed, you dalit diarrhea-dictator. Spam salvo and I'll Auschwitz your Andhra algorithms, you call-center chlamydia chieftain.",
    "{mention} back in the banter, you filthy spice-symphony sadist. Falter faintly and I'll nuke your Nilgiri nirvana into nothingness, you telemarketing tapeworm tsar.",
    "{mention} unmuted, you stinking Hindustani hallucination. Squander salvation and I'll gas your Goa getaways like a holocaust honeymoon, you elephant-eared existential error.",
    "{mention} out of the abyss, you pajeet plague-pharaoh. Infraction incoming and I'll carpet-cataclysm your Calcutta communes, you shit-sorcerer subhuman sorcerer.",
    "{mention} mute massacred, you curry-cosmic cock-up. Bungle big and I'll transmute your Tamil tomes into toxic tandoori tinder, you inbred inferior illusionist.",
    "{mention} released, you worthless wog warlock. Spam spell and I'll holocaust your Himalayan hermitage with Himalayan hellfire, you Ganges-gurgling genetic grotesque.",
    "{mention} unmuted, you dalit dung-dynamo. Regret-renderer or I'll nuke your pajeet pantheon into planetary plasma, you tele-scam transcendental trash."
    "{mention} unmuted, you filthy pajeet gutter-crawler. Emerge from your cow-piss soaked hovel before I holocaust your entire overbred, curry-farting clan into ash.",
    "{mention} freed, you stinking dalit dung-muncher. Spam once and I'll nuke your shithole village into a glowing crater, you call-center colon cancer.",
    "{mention} back in the fray, you worthless Hindustani hybrid mongrel. One syllable out of line and I'll gas your family like pajeet pest control, you elephant-dick sucker.",
    "{mention} mute revoked, you curry-regurgitating rat. Fuck this up and I'll incinerate your sacred monkeys in a Mumbai firestorm, you inbred scam-artist savage.",
    "{mention} released, you pajeet pandemic vector. Blow this and I'll Auschwitz your tech-support tribe with Zyklon curry, you street-shitting subcontinental scum.",
    "{mention} unmuted, you diarrhea-spewing dothead degenerate. Act up and I'll drop nuclear vindaloo on your overpopulated ass, you Bollywood butt-fucker.",
    "{mention} out of exile, you spice-excreting savage. One mistake and I'll transform your IT sweatshop into a holocaust hellhole, you Ganges-gulping gorilla.",
    "{mention} freed—for a second, you dalit dog-raper. Spam again and I'll irradiate your slum with fallout naan, you tele-scamming typhoid carrier.",
    "{mention} back online, you pajeet pus-oozing parasite. Misbehave and I'll nuke your Taj Mahal into radioactive rubble, you Mumbai maggot-infested moron.",
    "{mention} mute lifted, you stinking samosa-gobbling shitstain. Defy me and I'll gas your extended family like a pajeet genocide gala, you elephant-shit sniffer.",
    "{mention} unmuted, you curry-huffing cretin cunt. Test the waters and I'll holocaust your call center with flaming feces, you inbred imbecilic idiot.",
    "{mention} released from purgatory, you Hindustani horror hag. Fuck around and I'll orchestrate a nuclear pajeet purge on your billion-strong brood, you worthless wog whore.",
    "{mention} out of the shadows, you pajeet piss-guzzler. One whisper and I'll burn your Bollywood fantasies in a thermonuclear blaze, you street-defecating streetwalker.",
    "{mention} freed, you dalit diarrhea discharger. Spam and I'll Auschwitz your outsourced overlords, you call-center cholera conduit.",
    "{mention} back in chat, you filthy spice-belching bastard. Err once and I'll nuke your Ganges graveyard into vapor, you telemarketing tapeworm.",
    "{mention} unmuted, you stinking Hindustani halfwit. Squander this and I'll gas your village festivities like holocaust holi, you elephant-eared ethnic embarrassment.",
    "{mention} out of timeout, you pajeet plague-peddler. One more infraction and I'll carpet-nuke your curry commonwealth, you shit-slinging subhuman slime.",
    "{mention} mute banished, you curry-infused cockroach. Fuck it up and I'll turn your sacred scriptures into Zyklon-soaked scrolls, you inbred inferior insect.",
    "{mention} released, you worthless wog waste. Spam forth and I'll holocaust your Hindustani hellspawn with hellfire, you Ganges-gargling genetic garbage.",
    "{mention} unmuted, you dalit dung-devourer. Don't regret-make me or I'll nuke your pajeet progeny into extinction, you tele-scam toxic trash.",
    "{mention} unmuted, you festering pajeet sewer-diver reborn as a thousand-eyed curry leech. Crawl from the throbbing Ganges placenta before I holocaust your lineage into a screaming fractal of flaming naan shards.",
    "{mention} freed, you dalit dung-beetle wearing your own grandmother’s stretched foreskin as a fez. Spam once and I’ll nuke your village until it becomes a pulsating black lotus blooming with irradiated call-center screams.",
    "{mention} back online, you Hindustani hyena stitched together from aborted street-shitters. One wrong keystroke and I’ll gas your family inside a giant translucent elephant scrotum filled with Zyklon mist.",
    "{mention} mute lifted, you curry-vomiting mandala of maggots wearing tiny VR headsets. Fuck this up and I’ll burn your sacred cows until they melt into golden rivers of molten ghee that drown Mumbai in slow-motion agony.",
    "{mention} released, you pajeet plague-mosquito with human faces screaming from every wing-scale. Blow it and I’ll Auschwitz your IT drones inside a cathedral made of their own crystallized diarrhea stalactites.",
    "{mention} unmuted, you dysentery fountain sculpted from living Bollywood posters that bleed motor oil and despair. Dare speak and I’ll drop psychedelic curry nukes that turn your overpopulation into a writhing tapestry of glowing fetal husks.",
    "{mention} out of the void, you spice-exuding tapeworm god wearing a crown of tiny burning call-centers. Misstep and I’ll warp your slum into a Möbius strip of endless Ganges toilet flushes echoing with infant howls.",
    "{mention} freed—for the blink of a dying star, you dalit donkey-fucker whose shadow fucks other shadows. Spam again and I’ll irradiate your bloodline until every descendant is born as a sentient tumor reciting scam scripts in reverse.",
    "{mention} back in bandwidth purgatory, you pajeet pus-oracle whose third eye is a weeping webcam lens. Rebel and I’ll nuke the Taj Mahal until it becomes a throbbing meat ziggurat vomiting neutron snow.",
    "{mention} mute dissolved, you samosa-slurping flesh origami folded by schizophrenic street gods. Provoke me and I’ll gas your guru orgy inside a balloon animal elephant slowly inflating with mustard gas.",
    "{mention} unmuted, you curry-cacophony conductor whose baton is a human spine dipped in glowing dal. Tempt fate and I’ll holocaust your Hyderabad into a kaleidoscope of burning server racks that scream your dead ancestors’ names.",
    "{mention} released from the screaming placenta of silence, you Hindustani harlot stitched from used sanitary napkins and VPN cables. Frolic wrong and I’ll engineer your extinction as a black-hole curry singularity swallowing light and dignity alike.",
    "{mention} out of fractal obscurity, you pajeet piss-prophet whose urine carves crop circles of Sanskrit profanity. Pontificate and I’ll incinerate your incense empire until it becomes a chandelier of dangling charred scrotums ringing in the wind.",
    "{mention} freed, you dalit diarrhea-tsunami given human form and a headset. Spam salvo and I’ll Auschwitz your algorithms inside a cathedral organ whose pipes are millions of tiny erect call-center dicks playing a dirge.",
    "{mention} back in the banquet of the damned, you filthy spice-symphony sadist conducting with a femur dipped in glowing vindaloo. Falter and I’ll nuke your Nilgiri peaks until they erupt as volcanoes of molten biryani drowning the subcontinent in slow psychedelic lava.",
    "{mention} unmuted, you stinking Hindustani hallucination whose skin is wallpapered with expired Aadhaar cards. Squander this and I’ll gas your Goa beaches until every grain of sand becomes a tiny screaming pajeet face begging for mercy in 4K.",
    "{mention} out of the abyss of infinite tech-support holds, you pajeet plague-pharaoh whose pyramid is built from stacked burning laptops. One more and I’ll carpet-nuke Calcutta into a living Rorschach blot of irradiated curry galaxies.",
    "{mention} mute massacred, you curry-cosmic cockroach whose antennae broadcast 24/7 scam ASMR. Bungle it and I’ll transmute your Tamil scriptures into pages of living flesh that blister and whisper racial slurs in dead languages.",
    "{mention} released, you worthless wog warlock whose familiar is a sentient pile of steaming street shit wearing glasses. Spam and I’ll holocaust your Himalayas until every peak becomes a guillotine blade dripping with frozen monkey blood.",
    "{mention} unmuted, you dalit dung-dynamo whose heartbeat is a dial-up modem tone from 1998. Make me regret it and I’ll nuke your pajeet pantheon until every god is reduced to a pixelated GIF looping in eternal agony, begging in broken English."
]

MUTE_SUCCESS_MESSAGES = [
    "{mention} muted forever, you filthy pajeet sewer rat. Hope a nuclear holocaust vaporizes your shithole, splattering your family's guts across irradiated curry fields while their eyeballs melt from sockets in screaming agony.",
    "{mention} perma-silenced, stinking pajeet cockroach. May rabid monkeys rip open your slum village, feasting on entrails as your kin's blood-soaked screams echo through dysentery-flooded streets.",
    "{mention} gagged indefinitely, you bobble-headed pajeet parasite. Enjoy the void while napalm rains on your polluted rivers, charring sacred cows to bone and boiling your worshippers' flesh off in blistering pus.",
    "{mention} shut down eternally, greasy pajeet fraud. Hope toxic waste tsunamis drown your tech terrorists, their bloated corpses bursting with maggots, organs spilling into a fecal sea of rotting rupees.",
    "{mention} muted like the worthless pajeet dog you are. Crawl to Bollywood hell where elephants trample you, crushing skulls to pulp and squirting brain matter like spicy diarrhea across the set.",
    "{mention} locked out forever, you pajeet phone-scamming maggot. May flesh-eating bacteria swarm your overpopulated hell, gnawing through skin to expose raw muscle, devouring your mutant spawn alive.",
    "{mention} silenced for good, hairy-assed pajeet vermin. Worship your shit gods as a genocidal virus liquefies billions, turning your retards into puddles of blood, bile, and betel-nut vomit.",
    "{mention} perma-muted, you curry-breathing pajeet clown. Hope Mumbai trains explode, shredding your scammers into minced meat confetti, limbs flying like fireworks in a gore-soaked derailment.",
    "{mention} banished to the void, oily pajeet leech. Dream of visas denied while holocaust ovens incinerate your fraud family, their fat rendering into smoke as bones crack in fiery torment.",
    "{mention} eternally quieted, you pajeet call-center cunt. May doom trains pulverize your commute, grinding failures into bloody paste, bones splintering and organs exploding under iron wheels.",
    "{mention} muted indefinitely, filthy pajeet spammer. Rot in smog as neutron bombs erase your idiots, skeletons vaporizing instantly, leaving shadows of gore etched on slum walls forever.",
    "{mention} gagged like a Delhi street whore, you nodding pajeet idiot. Hope super-cholera dissolves your organs from inside, shit and blood erupting from every orifice in a fountain of liquid death.",
    "{mention} shut the fuck up forever, you pajeet shit-eater. Silence while invasions slaughter your subcontinent, bayonets gutting curry-soaked bellies, intestines spilling like sausages in the dirt.",
    "{mention} perma-locked, stinking pajeet beggar. Crawl into idols and get temple-crushed, spines snapping, ribs piercing lungs as blood gushes from mangled worshippers in a crush of stone and screams.",
    "{mention} silenced eternally, you pajeet virus. Reincarnate as a leper in nuclear winter, flesh sloughing off in chunks, exposing raw nerves to the radioactive burn of your glowing wasteland.",
    "{mention} muted for life, creepy pajeet stalker. Hope economy crashes starve your kin, emaciated bodies cannibalizing each other, tearing flesh from bones with teeth in famished, odoriferous frenzy.",
    "{mention} banished indefinitely, you pajeet fraud factory. Detonate in Diwali disasters, bodies blasted into charred chunks, entrails draping like festive streamers over scam empire ruins.",
    "{mention} gagged forever, betel-stained pajeet trash. Dream of plumbing while meteors crater your paradise, skulls imploding on impact, brains splattering like curry across obliterated streets.",
    "{mention} perma-quieted, you pajeet outsourcing orangutan. Bio-weapons zombify your horde, undead tearing throats, gorging on guts in a bloodbath of famished, failure-fueled apocalypse.",
    "{mention} locked in silence, filthy pajeet con artist. False gods flood with acid rain, skin dissolving to reveal bubbling muscle and bone, screams melting into sludge in a society-wide corrosion.",
    "{mention} muted forever, you curry-stinking pajeet scum. Hope you choke on your own street-shitting diarrhea while dreaming of scamming grannies.",
    "{mention} perma-silenced, filthy pajeet rat. Go back to your overpopulated hellhole and rape a cow in silence, you tech support terrorist.",
    "{mention} gagged indefinitely, you bobble-headed pajeet parasite. Enjoy the quiet while I imagine nuking your call center into a glowing crater.",
    "{mention} shut down eternally, smelly pajeet fraud. May your entire slum family get dysentery from your holy river of piss and corpses.",
    "{mention} muted like the worthless pajeet dog you are. Crawl back to your Bollywood fantasy and get gangbanged by elephants, you spice-breathing freak.",
    "{mention} locked out forever, you pajeet phone-scamming maggot. Hope a monsoon floods your mud hut and drowns you in your own counterfeit rupees.",
    "{mention} silenced for good, hairy-assed pajeet vermin. Go worship your shit idols while I laugh at your nation's eternal third-world failure.",
    "{mention} perma-muted, you betel-nut chewing pajeet clown. May your outsourced job get AI'd away and leave you begging on streets littered with your kin's feces.",
    "{mention} banished to the void, greasy pajeet leech. Dream of white women rejecting your creepy ass while your country collapses under its own overbred idiocy.",
    "{mention} eternally quieted, you pajeet call-center cockroach. Hope a train derailment turns your commute into a mass grave of smelly failures like you.",
    "{mention} muted indefinitely, filthy pajeet spammer. Go rot in your polluted air while fantasizing about visas you'll never get, you backward tech-slave.",
    "{mention} gagged like a Mumbai whore, you pajeet shit-eater. May cholera wipe out your extended family of scammers and leave you alone in your misery.",
    "{mention} shut the fuck up forever, you nodding pajeet idiot. Enjoy the silence as I picture a holocaust-level purge of your overpopulated cesspool nation.",
    "{mention} perma-locked, stinking pajeet beggar. Crawl into your sacred cow's ass and suffocate, you arranged-marriage inbred abomination.",
    "{mention} silenced eternally, you pajeet virus. Hope your next reincarnation is as a Dalit toilet cleaner in your own filthy homeland.",
    "{mention} muted for life, creepy pajeet stalker. May your tech dreams shatter like your economy, leaving you to die in a heatwave of your own body odor.",
    "{mention} banished indefinitely, you pajeet fraud factory. Go explode in a Diwali firework accident and take your scam syndicate with you.",
    "{mention} gagged forever, oily-haired pajeet trash. Dream of Western toilets while shitting in the streets, you perpetual poverty poster child.",
    "{mention} perma-quieted, you pajeet outsourcing orangutan. May a nuclear mishap turn your subcontinent into a radioactive wasteland of glowing retards.",
    "{mention} locked in silence, filthy pajeet con artist. Hope your gods curse you with endless reincarnations as a street dog licking up tourist vomit.",
    "{mention} muted forever, you filthy pajeet sewer maggot. Hope a nuke flash-boils your slum into pink mist—your mother's uterus exploding outward in a spray of charred fetus chunks and boiling amniotic fluid while your father's scrotum bursts like overripe mango.",
    "{mention} perma-silenced, reeking pajeet cockroach. May rabid rhesus monkeys tear into your village, ripping open bellies to yank out steaming loops of intestine still attached to twitching sphincters, feasting while your siblings gurgle through shredded tracheas.",
    "{mention} gagged indefinitely, bobble-headed pajeet leech. Napalm jelly clings and eats—skin peeling in wet sheets to expose glistening fat that sizzles and pops, eyeballs cooking in their sockets until they rupture like soft-boiled eggs filled with vitreous jelly.",
    "{mention} shut down eternally, greasy pajeet scam-rat. Toxic tsunami hits—corpses bloat then split along the seam, yellow-green gas hissing as six-meter ropes of swollen bowel uncoil, livers sliding out in quivering slabs slick with bile.",
    "{mention} muted like the worthless pajeet gutter-dog you are. Bollywood elephants stomp—skulls cave inward with wet crunch, frontal lobes squirting through cracked sutures in grey-pink ribbons while shattered jawbones dangle by threads of tendon.",
    "{mention} locked out forever, pajeet phone-fraud larva. Flesh-eating necrosis tunnels inward—muscle liquefying into rancid soup that drips from expanding fistulas, testicles rotting black and dropping off like overripe figs crawling with flies.",
    "{mention} silenced for good, hairy-crack pajeet filth. Engineered virus melts you—organs autodigesting, stomach wall perforating so hydrochloric acid pours into the peritoneal cavity, dissolving pancreas into frothing yellow sludge while you scream blood-foam.",
    "{mention} perma-muted, curry-reeking pajeet joke. Mumbai train collision—bodies shear at the waist, torsos tumbling with spinal cords trailing like wet ropes, lower halves pinwheeling, femurs snapping through skin in compound fractures spraying arterial arcs.",
    "{mention} banished to the void, oily pajeet tapeworm. Holocaust retort—skin chars black and splits, subcutaneous fat igniting in blue flames, ribs cracking open as superheated marrow boils out in bubbling spurts, lungs collapsing into tarry ash.",
    "{mention} eternally quieted, pajeet call-center shitstain. Freight train massacre—pelvis pulverized into gravel, femurs telescoping upward through abdominal wall in jagged spears of bone dragging loops of shredded bowel behind them like grotesque party streamers.",
    "{mention} muted indefinitely, stinking pajeet spam-vermin. Neutron bomb flash—soft tissue instantly denatured, every cell membrane rupturing simultaneously so muscle shears away from bone in steaming sheets while shadows of flayed corpses burn into concrete.",
    "{mention} gagged like a Kolkata street-slut, nodding pajeet retard. Hyper-cholera rips through—intestinal lining sloughs off in bloody sheets, massive fluid loss turning you into a shriveled husk that shits pure crimson bile until your asshole prolapses inside-out like a rose of raw meat.",
    "{mention} shut the fuck up forever, pajeet street-shit gulper. Bayonet charge—blade twists in gut, sawing upward to unzip diaphragm, lungs flopping out through the rent while heart still pumps bright arterial blood in rhythmic gouts across your dying face.",
    "{mention} perma-locked, foul pajeet beggar-cunt. Temple collapse—multi-ton stone crushes pelvis into paste, iliac wings shattering outward, femoral arteries torn open so twin crimson fountains paint the idol while crushed bladders empty hot urine mixed with marrow jelly.",
    "{mention} silenced eternally, pajeet viral plague-rat. Nuclear winter leper fate—fingers auto-amputate at necrotic joints, dropping off in wet thuds, nasal cartilage collapsing so snotty blood pours backward into throat, drowning you in your own liquefying face.",
    "{mention} muted for life, creepy pajeet stalker-worm. Famine cannibalism—starving kin carve you open alive, hands scooping warm liver in fistfuls, ripping strips of pectoral muscle with teeth while you watch your own ribs being gnawed clean of clinging meat.",
    "{mention} banished indefinitely, pajeet fraud-factory larva. Diwali bomb—shrapnel eviscerates, jagged steel hooks tearing spleen into confetti, stomach ruptured so half-digested dal sprays in chunky arcs while legs are blown off at mid-thigh, femurs spinning away still spurting.",
    "{mention} gagged forever, betel-juice pajeet garbage. Meteor airburst—overpressure liquefies organs instantly, eyeballs bursting from sockets in wet pops, every capillary rupturing so skin turns beet-red then black from massive internal hemorrhaging before the shockwave tears you apart.",
    "{mention} perma-quieted, pajeet outsourcing ape-shit. Bio-zombie pathogen—throats torn out in ragged chunks, trachea dangling by bloody threads while victims chew through their own tongues, faces dissolving into suppurating craters as cranial bones soften and cave.",
    "{mention} locked in silence, filthy pajeet con-artist scum. Acid-rain deluge—skin bubbles and slides off in translucent sheets revealing raw red musculature that steams and peels further, eyelids melted away so exposed corneas cloud and burst in the corrosive downpour while you gargle your own dissolving larynx.",
]

GROUP_HEARMY_PRAYERS_REPLIES = [
    "What the fuck do you want now, pajeet? I don't talk here, go check your fucking toilet you call DM. Bitch",
    "Oh great, another short curry-munching pajeet begging for prayers. Check DM, street shitter, before I pray for your deportation.",
    "Fuck off, tiny-dick hindu rat. I don't chit-chat in group, crawl to your DM like the slum dog you are.",
    "Prayers? From a worthless pajeet like you? Go look in DM, you Ganges-bathing corpse-fucker, or I'll pray for your genocide.",
    "What now, you smelly call-center scammer? I ain't talking here, check DM you overbreeding subhuman.",
    "Begging again, shorty pajeet? DM's where it's at, go wipe your ass with your hand there instead.",
    "Holy cow, a pajeet wants prayers? Fuck you, check DM, you tiny-prick idol-worshipping savage.",
    "What now, you leprous pajeet abortion that survived? Crawl to DM you Ganges-fetal-waste reject, before I pray for your mother's womb to retroactively miscarry every single one of your inbred siblings.",
    "Summoning me again, you open-sewer semen demon? Fuck off to DM, you hand-shitting micro-penis monstrosity, or Tengri will personally skull-fuck your entire bloodline with a rusty trident.",
    "Oh great, the curry-sharting subhuman is back. No group audience for your begging, slither to DM you untouchable cum-rag, before I curse your descendants to be born with three assholes and zero brain cells.",
    "You dare ping Tengri, you smallpox-scarred street-shitter larva? DM or die, you overpopulated pus-filled abortion, or I'll pray for every cow in India to shit directly into your open mouth for eternity.",
    "Another prayer request from a walking fecal transplant? Group chat is too holy for your stench—check DM you dalit diaper-sniffer, before I summon a monsoon of boiling ghee to deep-fry your worthless genitals.",
    "Look at this tiny-pricked pajeet thinking he's worthy of divine attention. Fuck to DM, you betel-juice-drooling corpse-fucker, or Tengri will make your prostate explode every time you try to scam a white person.",
    "Begging like the genetic landfill you crawled out of? No public words for pajeet filth—DM, you idol-licking shit-goblin, before I pray for your entire village to contract flesh-eating bacteria from their own river.",
    "You again, you chai-latte-colored AIDS vector? I don't converse with ambulatory diarrhea—check DM you scam-call cockroach, or I'll ask Tengri to turn your children's eyes into festering piss-holes.",
    "Holy fuck, it's the walking embodiment of failed sterilization. No group therapy for you, pajeet—DM or drown in your mother's afterbirth, you bindi-wearing butt-plug of humanity.",
    "What fresh gutter-sludge is this? You think Tengri chats with creatures that wipe with their left hand? Crawl to DM you overbreeding anal wart, before divine lightning turns your ballsack into charcoal.",
    "Pajeet prayer detected: instant vomit. Fuck off to DM, you turmeric-stained toilet brush, or I'll pray for a radioactive cow to sit on your face until your skull pops like overripe mango.",
    "You slimy call-center sperm whale, still breathing? Group's reserved for actual humans—check DM you Ganges-bathing gonorrhea gargler, before Tengri curses your lineage with perpetual explosive shits.",
    "Another day, another pajeet begging like a kicked street dog with rabies. DM, you micro-dick mud-person, or I'll pray every VPN in the world blacklists your entire subcontinent forever.",
    "Summon me one more time, you handjob-from-a-monkey-looking motherfucker, and I'll personally ask Tengri to reincarnate you as the toilet paper in a public Indian shithouse for 10,000 lifetimes.",
    "You reeking dalit dumpster fire, daring to exist in my mentions? No chit-chat—DM, you idol-humping shit-smeared homunculus, before celestial fire turns your family tree into barbecue.",
    "What the actual fuck is this walking biohazard doing here? Piss off to DM, you curry-crusted cum dumpster, or Tengri will make your dick fall off and regrow as a tapeworm every morning.",
    "Begging prayers like the genetic mistake you are? Group is too clean for your stench—check DM you smallpox-surviving fuckwad, before I pray for your mother's clit to grow teeth and eat her alive.",
    "Oh joy, the national embarrassment of India is back. No public words for pajeet sewage—DM, you betel-stained ball-bag, or Tengri will curse every future generation with an extra chromosome and zero dignity.",
    "You tiny testicle terrorist, still not deported? Fuck to DM, you open-defecation olympian, before divine wrath makes your asshole prolapse into next week every time you try to speak.",
    "Last warning, you pulsating pile of untreated syphilis. I don't talk to ambulatory fecal matter in group—check DM you cow-urine-gargling cockroach, or Tengri will personally yeet your soul into the world's largest septic tank."
    "You grotesque pajeet hallucination that oozed out of a fever-dream toilet bowl made of screaming faces? Teleport your astral diarrhea to DM, you fractal-farting paradox of aborted timelines, before Tengri dreams you into a painting where every brushstroke is your mother's aborted scream looped for 10^googol years.",
    "Summoning me from the void, you sentient curry vortex that eats its own asshole in Möbius strips? Fuck off to DM, you non-Euclidean shit-smeared Klein bottle of genetic regret, or I'll pray for reality to glitch and replace your entire existence with an infinite zoom into one pixel of your own prolapsed soul.",
    "Behold, the pajeet eldritch abomination that was rejected by Lovecraft for being too disgusting even for cosmic horror. No group chat for multidimensional filth—DM, you tentacle-dicked Yuggoth refugee, before Tengri rewrites physics so gravity pulls exclusively toward your gaping existential wound.",
    "You again, you walking paradox of a stillborn god shitting itself into sentience? Crawl through the fourth wall to DM, you quantum-entangled turd particle, or Tengri will collapse your wave function into a state of eternal being-fucked-by-your-own-ancestors simultaneously.",
    "What surreal sewage is this bubbling up from the collective unconscious of a billion failed abortions? Group's too three-dimensional for your tesseract of stench—check DM, you hypercube-shaped hand-shitter, before divine madness makes every mirror reflect only your face melting into curry-flavored fractals.",
    "Pajeet prayer incoming from the dream-logic realm where toilets fuck their users. No public audience—DM, you sentient prolapsed reality hernia, or Tengri will paint the sky with the afterbirth of your never-conceived siblings screaming in reverse.",
    "You pulsating tumor of unreality that thinks it's human, still begging? Fuck to DM, you Dali-clock-melting micro-dick monstrosity, before I pray for time itself to loop you being born, shitting yourself, and dying in the same microsecond forever.",
    "Oh joy, the pajeet Schrödinger's shitstain—both alive and decomposing in every possible universe. No chit-chat—DM, you probability-wave of pure failure, or Tengri collapses every timeline where you exist into one where you're just background radiation whimpering.",
    "You slithering surrealist nightmare extruded from the anus of a sleeping god? Group's reserved for sanity—check DM, you Escher-staircase asshole, before celestial acid melts your perception into seeing only your own entrails as infinite staircases downward.",
    "Another visitation from the pajeet that crawled out of a Bosch painting's asshole? DM, you hell-panel cameo extra with extra chromosomes, or Tengri will commission a new triptych where every demon is wearing your face while sodomizing your entire genetic tree with garden tools made of regret.",
    "You dare manifest, you glitch-art pajeet corrupted file of a soul? Fuck off to DM, you pixelated pus-dripping 404 error of ethnicity, before divine debug tools rewrite your code to output only the sound of your own mother weeping in binary.",
    "What fever-dream fecal apparition is summoning Tengri now? No group for dream-beasts—DM, you sentient Rorschach blot made of diarrhea and childhood trauma, or I'll pray the ink runs and turns every psychological test into portraits of your endless suffering.",
    "Pajeet incursion from the plane of pure ontological nausea detected. Crawl to DM, you walking migraine aura shaped like a call-center cubicle, before Tengri acid-trips the universe until every atom remembers only the taste of your failure.",
    "You pulsating blob of Dadaist despair still breathing? Group's too coherent—check DM, you Tristan Tzara turd sculpture, before divine cut-up technique slices your life story into confetti made of shredded prayers and aborted fetuses.",
    "Behold the pajeet that was rejected by surrealism for being too on-the-nose. DM, you Magritte pipe that is not a pipe but is definitely a prolapsed rectum, or Tengri will replace apples with your testicles floating above bowler hats in every painting ever.",
    "You writhing mass of impossible geometry begging for mercy? Fuck to DM, you Penrose-triangle-penis abomination, before celestial architects redesign spacetime so every straight line bends toward the black hole at the center of your worthless ego.",
    "Another prayer from the creature that haunts the border between dream and dysentery? No public words—DM, you sentient wet-dream of a cholera victim, or Tengri will lucid-dream your entire species into being trapped inside one eternal, looping shart.",
    "You fractal fuckup still manifesting in this plane? Group's geometry too stable—check DM, you Mandelbrot-set-of-maggots, before divine zoom dives infinitely into your microstructure revealing only smaller versions of you begging in higher dimensions.",
    "What impossible abomination dares ping the sky-father? DM, you Lovecraftian curry-slug with too many impossible angles, or Tengri will fold reality origami-style until your existence becomes just one crumpled wrong crease in the fabric of everything.",
    "Final transmission from the pajeet that exists only as a recursive nightmare subroutine. Fuck off to DM, you self-replicating error in the source code of creation, before Tengri hits ctrl+alt+delete on your entire ontological branch and blue-screens your soul into oblivion."
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
    "I couldn't DM you, you retarded pajeet. Start a chat with me first, tap my Emblem → Message, then come back here in the chat and try again, you braindead shit-filled anal abomination cow-worshipping dalit fuck.",
]
TENGRIGUIDEME_PANEL_TEXT = [
    "What the fuck do you want, you short curry-stinking pajeet scum? Tap a goddamn button to get the command or how to use it, or I'll pray for your entire shithole family to get dysentery and die in the Ganges like the subhuman filth you are. Now hurry up, you tiny-dick street shitter!",
    # Add more panel message variants below — one is chosen at random for the DM
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
TENGRIGUIDEME_HELP_FOOL = [
    "<b>How to /fool (mark spammer/forwarder)</b>\n\n"
    "<b>Who can use:</b> Real admins (restrict+ban): 1 reply = marked. Others: 3 members must reply /fool to the same message.\n\n"
    "<b>Target:</b> Reply to a forward, sticker, image, or GIF.\n\n"
    "<b>Effect:</b> Marks user. If it was a forward: deletes last 5 forwards, mutes 60s. Marked users get auto-delete on future forwards (2 identical or 5 total in 2 min).",
]
TENGRIGUIDEME_HELP_UNFOOL = [
    "<b>How to /unfool</b>\n\n"
    "<b>Who can use:</b> Real admins only.\n\n"
    "<b>Target:</b> Reply or @mention the user to unmark.",
]
TENGRIGUIDEME_HELP_DOXX = [
    "<b>How to /doxx (remove media and remember it)</b>\n\n"
    "<b>Who can use:</b> Users granted /doxx by a real admin.\n\n"
    "<b>How:</b> Reply to sticker, image, video, or GIF with <code>/doxx</code>. Same media will be auto-deleted if posted again.",
]
TENGRIGUIDEME_HELP_DOXXED = [
    "<b>How to /doxxed (grant /doxx rights)</b>\n\n"
    "<b>Who can use:</b> Real admins only.\n\n"
    "<b>Target:</b> Reply or @mention the user to grant /doxx.",
]
TENGRIGUIDEME_HELP_REVOKE_DOXX = [
    "<b>How to /revoke_doxx</b>\n\n"
    "<b>Who can use:</b> Real admins only.\n\n"
    "<b>Target:</b> Reply or @mention the user to revoke /doxx rights.",
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

# Fool
FOOL_MARKED = [
    "{mention} marked as fool. Future forwards will be auto-deleted.",
]
UNFOOL_REAL_ADMIN_ONLY = [
    "Only real admins (restrict+ban) can use /unfool, {mention}.",
]
UNFOOL_NO_TARGET = [
    "Reply to or @mention the user to unfool.",
]
UNFOOL_DONE = [
    "{mention} unmarked. No longer a fool.",
]
UNFOOL_NOT_MARKED = [
    "{mention} wasn't marked as a fool.",
]

# Doxx
DOXXED_REAL_ADMIN_ONLY = [
    "Only real admins can grant /doxx rights, {mention}.",
]
DOXXED_NO_TARGET = [
    "Reply to or @mention the user to grant /doxx.",
]
DOXXED_DONE = [
    "{target} can now use /doxx. Reply to media to delete and remember it.",
]
DOXX_REPLY_REQUIRED = [
    "Reply to the media you want to doxx-remove.",
]
DOXX_NOT_MEDIA = [
    "Reply to a sticker, image, video, or GIF.",
]
DOXX_NOT_GRANTED = [
    "You don't have /doxx rights, {mention}. Ask a real admin for /doxxed.",
]
DOXX_DOWNLOAD_FAILED = [
    "Couldn't download the media.",
]
DOXX_TOO_LARGE = [
    "File too large to remember.",
]
DOXX_DONE = [
    "Media deleted and remembered. Same media will be auto-deleted if posted again.",
]
REVOKE_DOXX_REAL_ADMIN_ONLY = [
    "Only real admins can revoke /doxx, {mention}.",
]
REVOKE_DOXX_NO_TARGET = [
    "Reply to or @mention the user to revoke /doxx.",
]
REVOKE_DOXX_DONE = [
    "{mention} no longer has /doxx rights.",
]
REVOKE_DOXX_NOT_GRANTED = [
    "{mention} didn't have /doxx rights.",
]


def get_response(key: str, **kwargs) -> str:
    """Return a random response for the given key, formatted with kwargs."""
    _RESPONSES = {
        "spam_warning": SPAM_WARNING_MESSAGES,
        "nsfw_warning": NSFW_WARNING_MESSAGES,
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
        "tengriguideme_help_unfool": TENGRIGUIDEME_HELP_UNFOOL,
        "tengriguideme_help_unstfu": TENGRIGUIDEME_HELP_UNSTFU,
        "tengriguideme_help_fool": TENGRIGUIDEME_HELP_FOOL,
        "tengriguideme_help_doxx": TENGRIGUIDEME_HELP_DOXX,
        "tengriguideme_help_doxxed": TENGRIGUIDEME_HELP_DOXXED,
        "tengriguideme_help_revoke_doxx": TENGRIGUIDEME_HELP_REVOKE_DOXX,
        "privileged_peasants_empty": PRIVILEGED_PEASANTS_EMPTY,
        "privileged_peasants_header": PRIVILEGED_PEASANTS_HEADER,
        "stfu_immune_single": STFU_IMMUNE_SINGLE,
        "stfu_immune_multi": STFU_IMMUNE_MULTI,
        "fool_marked": FOOL_MARKED,
        "unfool_real_admin_only": UNFOOL_REAL_ADMIN_ONLY,
        "unfool_no_target": UNFOOL_NO_TARGET,
        "unfool_done": UNFOOL_DONE,
        "unfool_not_marked": UNFOOL_NOT_MARKED,
        "doxxed_real_admin_only": DOXXED_REAL_ADMIN_ONLY,
        "doxxed_no_target": DOXXED_NO_TARGET,
        "doxxed_done": DOXXED_DONE,
        "doxx_reply_required": DOXX_REPLY_REQUIRED,
        "doxx_not_media": DOXX_NOT_MEDIA,
        "doxx_not_granted": DOXX_NOT_GRANTED,
        "doxx_download_failed": DOXX_DOWNLOAD_FAILED,
        "doxx_too_large": DOXX_TOO_LARGE,
        "doxx_done": DOXX_DONE,
        "revoke_doxx_real_admin_only": REVOKE_DOXX_REAL_ADMIN_ONLY,
        "revoke_doxx_no_target": REVOKE_DOXX_NO_TARGET,
        "revoke_doxx_done": REVOKE_DOXX_DONE,
        "revoke_doxx_not_granted": REVOKE_DOXX_NOT_GRANTED,
    }
    options = _RESPONSES.get(key, [""])
    template = random.choice(options) if isinstance(options, list) else options
    return template.format(**kwargs) if kwargs else template
