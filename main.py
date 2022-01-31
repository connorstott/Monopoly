from colorama import Fore, Back, Style
from enum import Enum, auto
import random
import time
import os

class Player():
	def __init__(self, letter: str):
		self.letter = letter
		self.position = 0
		
		self._total_money = 1500

		self.dice_total = 0
		self.in_jail = False
		self.jail_turns = 3
	
	def setBoardDisplayer(self, board_displayer) -> None:
		self._board_displayer = board_displayer
	
	def getTotalMoney(self) -> int:
		return self._total_money
	
	def payMoney(self, amount: int, show_text: bool = True):
		self._total_money -= amount
		if show_text: print(f"You have spent {Fore.RED}£{amount}{Fore.RESET}\nNew balance: {Fore.LIGHTYELLOW_EX}£{self._total_money}{Fore.RESET}")
	
	def giveMoney(self, amount: int, show_text: bool = False):
		self._total_money += amount
		if show_text: print(f"\nNew balance: {Fore.LIGHTYELLOW_EX}£{self._total_money}{Fore.RESET}")

	def turn(self) -> None:
		double = True
		double_count = 0
		escaped = False

		if self.jail_turns == 0 and self.in_jail: 
			self.printHeading()
			self.getOutJail()
		if self.in_jail:
			escaped = self.jail()
			if not escaped: return

		while double:
			self.printHeading()
			self.enterPrompt("roll the die")
			double = self.diceRoll()
			if escaped: double = False # can't do a double roll if you've escaped jail this turn
			#self.dice_total = 17
			#double = True
			double_count += 1 if double else 0

			if double_count == 3:
				print(f"{Fore.RED+Back.BLACK}You were going so fast that the police think you're botting, so sent you to jail.{Style.RESET_ALL}")
				self.goToJail()
				self.enterPrompt("go to jail")
				return

			self.enterPrompt("move")
			self.move()
			
			self.standingInfo()
			self.standingAction()
			if self.in_jail: return # in case you land on go to jail when you rolled a double
	
	def printHeading(self) -> None:
		self._board_displayer.printBoard()
		print(f"\n{Back.WHITE+Style.BRIGHT+Fore.BLACK} PLAYER '{self.letter}' {Style.RESET_ALL} {Style.BRIGHT}Balance: {Fore.LIGHTYELLOW_EX}£{self.getTotalMoney()}{Style.RESET_ALL}\n")
	
	def enterPrompt(self, action: str) -> None:
		input(f"press {Style.BRIGHT + Fore.YELLOW}[ENTER]{Style.RESET_ALL} to {action}: ")

	def diceRoll(self) -> bool:
		"""makes+stores the dice total and returns if double"""
		roll1, roll2 = random.randint(1,6), random.randint(1,6)
		double = True if roll1 == roll2 else False
		self.printHeading()
		print(f"[{roll1}] [{roll2}]" if not double else f"[{roll1}] [{roll2}] {Fore.BLUE}DOUBLE!{Fore.RESET}")

		total_roll = roll1 + roll2
		print(f"you rolled for {Style.BRIGHT + Fore.GREEN}{total_roll}{Style.RESET_ALL}!\n")

		self.dice_total = total_roll
		return double
	
	def move(self) -> None:
		for i in range(1, self.dice_total+1):
			self.position += 1
			if self.position == len(board): 
				self.passGo()
			self.printHeading()
			time.sleep(0.25)
	
	def passGo(self) -> None:
		self.position = board[0].position
		self.printHeading()
		print(f"You passed go! Collecting {Fore.GREEN}£200{Fore.RESET}!\n")
		self.giveMoney(200)
		self.enterPrompt("continue moving")
	
	def goToJail(self) -> None:
		self.in_jail = True
		self.position = 10
		self.jail_turns = 3
	
	def jail(self) -> bool:
		"""return whether or not you escape"""
		self.printHeading()
		self.enterPrompt("roll to try to escape")
		double = self.diceRoll()
		if double: self.getOutJail()
		else: self.enterPrompt("suffer")

		self.jail_turns -= 1
		return True if double else False
	
	def getOutJail(self) -> None:
		self.in_jail = False
		print("You're free!")
		self.enterPrompt("escape")

	def standingInfo(self) -> None:
		"""displays the info for the place it's standing on"""
		self.printHeading()
		try: board[self.position].standingInfo()
		except AttributeError: print("this hasn't been coded yet so it's empty. but coming very soon")
	
	def buyPlace(self, prompt_name: str) -> None:
		while True:
			buy = input(f"Do you want to buy this {prompt_name}? [Y/N]: ").lower()
			if buy == "y" or buy == "n": break
		if buy == "y": 
			self.payMoney(board[self.position].cost)
			board[self.position].owner = self
	
	def payRent(self) -> None:
		print(f"Giving {Back.BLACK}'{board[self.position].owner.letter}'{Back.RESET} their rent.")
		self.payMoney(board[self.position].rent)
		board[self.position].owner.giveMoney(board[self.position].rent)
	
	def payUtilityRent(self) -> None:
		print(f"Giving {Back.BLACK}'{board[self.position].owner.letter}'{Back.RESET} their rent.")
		self.payMoney(self.dice_total * board[self.position].dice_multiplier)
		board[self.position].owner.giveMoney(self.dice_total * board[self.position].dice_multiplier)
	
	def place_CanBuy(self, place: object) -> bool:
		"""returns whether you're able to buy a place"""
		return True if place.owner == None and self.getTotalMoney() >= place.cost else False
	
	def place_OtherOwned(self, place: object) -> bool:
		"""returns whether another player owns the place"""
		return True if place.owner != None and place.owner != self else False

	def standingAction(self) -> None:
		"""logic for when you land on a place (pay rent, buy it, nothing)"""
		place = board[self.position]
		if isinstance(place, Property):
			if self.place_CanBuy(place):
				self.buyPlace("Property")
			elif self.place_OtherOwned(place):
				self.payRent()

		elif isinstance(place, Station):
			if self.place_CanBuy(place):
				self.buyPlace("Station")
			elif self.place_OtherOwned(place):
				self.payRent()

		elif isinstance(place, Utility):
			if self.place_CanBuy(place):
				self.buyPlace("Utility")
			elif self.place_OtherOwned(place):
				self.payUtilityRent()

		elif isinstance(place, GoToJail):
			self.goToJail()

		elif isinstance(place, TaxPlace):
			self.payMoney(place.to_pay)

		elif isinstance(place, CommunityChestManager):
			place.getChest(self)

		print("")
		self.enterPrompt("finish turn")

board = [None]*40

class ColourTypes(Enum):
	BROWN = auto()
	LIGHTBLUE = auto()
	PINK = auto()
	ORANGE = auto()
	RED = auto()
	YELLOW = auto()
	GREEN = auto()
	DARKBLUE = auto()

def colourTypeToBack(colour: ColourTypes) -> str:
	"""returns the back colour as a string"""
	if colour == ColourTypes.BROWN: return Back.YELLOW
	elif colour == ColourTypes.LIGHTBLUE: return Back.LIGHTBLUE_EX
	elif colour == ColourTypes.PINK: return Back.LIGHTRED_EX
	elif colour == ColourTypes.ORANGE: return Back.LIGHTMAGENTA_EX
	elif colour == ColourTypes.RED: return Back.RED
	elif colour == ColourTypes.YELLOW: return Back.LIGHTYELLOW_EX
	elif colour == ColourTypes.GREEN: return Back.GREEN
	elif colour == ColourTypes.DARKBLUE: return Back.BLUE

class Property():
	def __init__(self, name: str, position: int, colour: ColourTypes, 
							 cost: int, house_cost: int, rent: int):
		self.name = name
		self.position = position
		self.colour = colour
		self.cost = cost
		self.house_cost = house_cost
		self.hotel_cost = house_cost
		self.rent = rent

		self._houses = 0
		self._hotels = 0

		self.owner = None
	
	def standingInfo(self) -> None:
		"""displays the info of the property when a player stands on it"""
		print(f"{colourTypeToBack(self.colour) + Style.BRIGHT + Fore.BLACK} You have arrived at: {self.name} {Style.RESET_ALL}")
		try: owner = self.owner.letter
		except AttributeError: owner = "Nobody"
		print(f"{Back.BLACK} owned by: '{owner}' {Style.RESET_ALL}\n")

		print(f"{Style.BRIGHT}  PRICE:       {Fore.RED}£{self.cost}{Style.RESET_ALL}")
		print(f"{Style.BRIGHT}  RENT:        {Fore.GREEN}£{self.rent}{Style.RESET_ALL}")
		print(f"{Style.BRIGHT}  HOUSE COST:  {Fore.BLUE}£{self.house_cost}{Style.RESET_ALL}")
		print(f"{Style.BRIGHT}  HOTEL COST:  {Fore.BLUE}£{self.house_cost}{Style.RESET_ALL}\n")

def createProperties() -> list:
	okr = Property("Old Kent Road", 1, ColourTypes.BROWN, 60, 50, 2)
	wr = Property("Whitechapel Road", 3, ColourTypes.BROWN, 60, 50, 4)
	tai = Property("The Angel, Islington", 6, ColourTypes.LIGHTBLUE, 100, 50, 6)
	er = Property("Euston Road", 8, ColourTypes.LIGHTBLUE, 100, 50, 6)
	pr = Property("Pentonville Road", 9, ColourTypes.LIGHTBLUE, 120, 50, 8)
	pm = Property("Pall Mall", 11, ColourTypes.PINK, 140, 100, 10)
	w = Property("Whiteahall", 13, ColourTypes.PINK, 140, 100, 10)
	na = Property("Northumberland Avenu", 14, ColourTypes.PINK, 160, 100, 12)
	bws = Property("Bow Street", 16, ColourTypes.ORANGE, 180, 100, 14)
	ms = Property("Marlborough Street", 18, ColourTypes.ORANGE, 180, 100, 14)
	vs = Property("Vine street", 19, ColourTypes.ORANGE, 200, 100, 16)
	s = Property("Strand", 21, ColourTypes.RED, 220, 150, 18)
	fs = Property("Fleet Street", 23, ColourTypes.RED, 220, 150, 18)
	ts = Property("Trafalgar Square", 24, ColourTypes.RED, 240, 150, 20)
	ls = Property("Leicester Square", 26, ColourTypes.YELLOW, 260, 150, 22)
	cs = Property("Coventry Street", 27, ColourTypes.YELLOW, 260, 150, 22)
	p = Property("Piccadilly", 29, ColourTypes.YELLOW, 180, 150, 24)
	rs = Property("Regent Street", 31, ColourTypes.GREEN, 300, 200, 26)
	os = Property("Oxford Street", 32, ColourTypes.GREEN, 300, 200, 26)
	bds = Property("Bond Street", 34, ColourTypes.GREEN, 320, 200, 28)
	pl = Property("Park Lane", 37, ColourTypes.DARKBLUE, 350, 200, 35)
	m = Property("Mayfair", 39, ColourTypes.DARKBLUE, 400, 200, 39)

	return [okr, wr, tai, er, pr, pm, w, na, bws, ms, vs, s, fs, ts, ls, cs, p, rs, os, bds, pl, m]

class Station():
	def __init__(self, name: str, position: int):
		self.name = name
		self.position = position

		self.cost = 200
		self.rent = 25

		self.owner = None
	
	def standingInfo(self) -> None:
		print(f"{Back.WHITE+Style.BRIGHT+Fore.BLACK} You have arrived at: {self.name} {Style.RESET_ALL}")
		try: owner = self.owner.letter
		except AttributeError: owner = "Nobody"
		print(f"{Back.BLACK} owned by: '{owner}' {Style.RESET_ALL}\n")

		print(f"{Style.BRIGHT}  PRICE:       {Fore.RED}£{self.cost}{Style.RESET_ALL}")
		print(f"{Style.BRIGHT}  RENT:        {Fore.GREEN}£{self.rent}{Style.RESET_ALL}\n")

def createStations() -> list:
	ls = Station("Liverpool St. Station", 5)
	m = Station("Marylebone Station", 15)
	fs = Station("Fenchurch St. Station", 25)
	kc = Station("King's Cross Station", 35)

	return [ls, m, fs, kc]

class Utility():
	def __init__(self, name: str, position: int):
		self.name = name
		self.position = position

		self.dice_multiplier = 4

		self.cost = 150
		self.owner = None
	
	def standingInfo(self) -> None:
		print(f"{Back.WHITE+Style.BRIGHT+Fore.BLACK} You have arrived at: {self.name} {Style.RESET_ALL}")
		try: owner = self.owner.letter
		except AttributeError: owner = "Nobody"
		print(f"{Back.BLACK} owned by: '{owner}' {Style.RESET_ALL}\n")

		print(f"{Style.BRIGHT}  PRICE: {Fore.RED}£{self.cost}{Style.RESET_ALL}")
		print(f"{Style.BRIGHT}  RENT if 1 utility owned: {Fore.BLUE}4x dice total{Style.RESET_ALL}")
		print(f"{Style.BRIGHT}  RENT if both utilities owned: {Fore.BLUE}10x dice total{Style.RESET_ALL}\n")

def createUtilities() -> list:
	ec = Utility("Electric Company", 12)
	ww = Utility("Water Works", 28)

	return [ec, ww]

class Go():
	def __init__(self):
		self.position = 0
	
	def standingInfo(self):
		print("You landed on go. Nothing happens")

class Jail():
	def __init__(self):
		self.position = 10
	
	def standingInfo(self):
		print("Just vising Jail")

class FreeParking():
	def __init__(self):
		self.position = 20
	
	def standingInfo(self):
		print("Free parking!")

class TaxPlace():
	def __init__(self, tax_type: str, position: int, to_pay: int):
		self.tax_type = tax_type
		self.position = position
		self.to_pay = to_pay
	
	def standingInfo(self):
		print(f"Paying {self.tax_type} tax of {Fore.RED}£{self.to_pay}{Fore.RESET}\n")

class GoToJail():
	def __init__(self):
		self.position = 30

		self.crimes = ["committing tax fraud", "punching babies", "walking slowly in front of people", "shopping for NFTs", "unironically watching ben shapiro", "не подчиняясь Родине", "caring about elon musk", "using facebook", "simping for FNAF animatronics", "watching dreamSMP", "telling people the wordle answer", "thinking 'oh no our table is broken' is funny", "vacuuming after 1pm on a Sunday", "having a stash of over-the-counter decongestant pills that could be used to make methamphetamine", "doing nothing", "watching tommyinnit", "being a weeb", "agreeing with jordan peterson", "ne pas se rendre", "being a man with a podcast", "watching joe rogan", "not being an alpha female", "alienating the worker from the means of production", "hating silco", "carrying a plank of wood down the street"]
	
	def standingInfo(self):
		print(f"Uh oh! The police found you {Fore.RED+Back.BLACK}{random.choice(self.crimes)}{Style.RESET_ALL}! They have decided to put you in jail!")

class CommunityChest():
	def __init__(self, description: str):
		self.description = description

		self.player = None
	
	def play(self, player: object):
		print("	" + self.description)
		self.player = player

		self.actions()
	
class goChest(CommunityChest):
	def __init__(self):
		description = f"Advance to go (Collect {Fore.GREEN}£200{Fore.RESET})"
		super().__init__(description)
	
	def actions(self):
		self.player.position = 0
		self.player.giveMoney(200, True)
	
class collectChest(CommunityChest):
	def __init__(self, description: str, collect_amount: int):
		description = f"{description}. Collect {Fore.GREEN}£{collect_amount}{Fore.RESET}"
		super().__init__(description)
		self.collect_amount = collect_amount
	
	def actions(self):
		self.player.giveMoney(self.collect_amount, True)

class payChest(CommunityChest):
	def __init__(self, description: str, pay_amount: int):
		description = f"{description}. Pay {Fore.RED}£{pay_amount}{Fore.RESET}\n"
		super().__init__(description)
		self.pay_amount = pay_amount
	
	def actions(self):
		self.player.payMoney(self.pay_amount)

class jailChest(CommunityChest):
	def __init__(self):
		super().__init__(f"{Fore.RED} Go to jail. Go directly do jail, do not pass Go, do not collect £200{Fore.RESET}")
	
	def actions(self):
		self.player.goToJail()

class collectPlayersChest(CommunityChest):
	def __init__(self, player_list: list, description: str, collect_amount: int):
		description = f"{description}. Collect {Fore.GREEN}£{collect_amount}{Fore.RESET} from every player"
		super().__init__(description)
		self.player_list = player_list
		self.collect_amount = collect_amount
	
	def actions(self):
		self.player_list.remove(self.player)
		for player in self.player_list:
			player.payMoney(self.collect_amount, False)
			self.player.giveMoney(self.collect_amount)
		self.player_list.append(self.player)

def makeCommunityChests(player_list: list):
	player_list = player_list.copy()
	cc1 = goChest()
	cc2 = collectChest("Bank error in your favour", 200)
	cc3 = payChest("Doctor's fee", 50)
	cc4 = collectChest("Stock sale", 50)
	cc6 = jailChest()
	cc7 = collectChest("Holiday fund matures", 100)
	cc8 = collectChest("Income tax refund", 20)
	cc9 = collectPlayersChest(player_list, "It's your birthday", 10)
	cc10 = collectChest("Life insurance matures", 100)
	cc11 = payChest("Pay hospital fees", 100)
	cc12 = payChest("Pay school fees", 50)
	cc13 = collectChest("Receive consultancy fee", 25)
	cc15 = collectChest("You have won second prize in a beauty contest", 10)
	cc16 = collectChest("You inherit £100", 100)

	return [cc1,cc2, cc3, cc4, cc6, cc7, cc8, cc9, cc10, cc11, cc12, cc13, cc15, cc16]

class CommunityChestManager():
	def __init__(self, position: int, community_chests: list):
		self.position = position
		self.community_chests = community_chests
	
	def standingInfo(self):
		print(f"{Back.LIGHTBLUE_EX+Fore.BLACK+Style.BRIGHT} You landed on a community chest! {Style.RESET_ALL}")
	
	def getChest(self, player: object):
		chest = random.choice(self.community_chests)
		chest.play(player)

class BoardDisplayer():
	def __init__(self):
		self._player_list = []
	
	def setPlayerList(self, player_list: list) -> None:
		self._player_list = player_list

	def getBackColour(self, place) -> str:
		try: colour = colourTypeToBack(place.colour)
		except AttributeError: colour = Back.WHITE

		return colour

	def getPlayerSymbol(self, player_list: list, board_index: int) -> str:
		"""returs the symbol for the player(s) on the specific board number"""
		players_at_pos = [player for player in player_list if player.position == board_index]
		if len(players_at_pos) == 0: player = " "
		elif len(players_at_pos) == 1: 
			player = players_at_pos[0].letter if players_at_pos[0].in_jail == False else Fore.RED + players_at_pos[0].letter
		else: player = "#"
		return Fore.BLACK + player + Fore.RESET

	def getSquare(self, board_index: int, player_list: list) -> str:
		"""returns the board square for the board number"""
		colour = self.getBackColour(board[board_index])
		player_symbol = self.getPlayerSymbol(player_list, board_index)
		return colour + f" {player_symbol} " + Back.RESET

	def printBoard(self) -> None:
		total_string = ""

		for i in range(20, 31): # top bar
			total_string += self.getSquare(i, self._player_list)
		total_string += "\n"
		
		for i in range(1, 10): # side bars
			total_string += self.getSquare(20-i, self._player_list)
			total_string += "   " * 9
			total_string += self.getSquare(30+i, self._player_list)
			total_string += "\n"

		for i in range(10, -1, -1): # bottom bar
			total_string += self.getSquare(i, self._player_list)
		
		os.system('clear')
		print(total_string)

def enterPlayer(player_list, used_characters, player_num = None) -> str:
	if player_num != None: player_num += 1 # for display, as index 0 = 1
	
	while True:
		player_num = len(player_list)+1 if player_num == None else player_num
		choice = input(f"player {player_num}'s letter: ")
		if len(choice) == 1 and choice not in used_characters and choice != "#": 
			return choice
		elif len(choice) != 1: 
			print(Fore.RED + "can only be 1 character long." + Fore.RESET)
		elif choice in used_characters: 
			print(Fore.RED + "letter already used by another player." + Fore.RESET)
		elif choice == "#":
			print(Fore.RED + "unavailable character" + Fore.RESET)

def pickPlayer(player_list) -> int:
	"""displays a list of players and their letters to choose from. if an invalid choice is sent return None"""
	[print(f"[player {i+1}] '{player_list[i].letter}'") for i in range(len(player_list))]

	player_num = input("\nplayer number : ")
	if player_num.isnumeric() and 1 <= int(player_num) <= len(player_list):
		player_num = int(player_num) - 1
	else: player_num = None
	return player_num

def createPlayers() -> list:
	player_list = []
	used_characters = []
	menu_state = "add player"

	while True: # add player menu loop
		os.system('clear')
		print(Back.WHITE + Style.BRIGHT + Fore.BLACK + f" {menu_state.upper()} " + Style.RESET_ALL + "\n")
			
		if menu_state == "main menu":
			choice = input("[1] Enter another player\n[2] Edit a player's letter\n[3] Delete a player\n[4] Finish adding\n\n : ")
			if choice.isnumeric() and 1 <= int(choice) <= 4:
				choice = int(choice)
				if choice == 1: menu_state = "add player"
				elif choice == 2: menu_state = "edit player"
				elif choice == 3: menu_state = "delete player"
				elif choice == 4: break

		elif menu_state == "add player":
			player_letter = enterPlayer(player_list, used_characters)
			player_list.append(Player(player_letter))
			used_characters.append(player_letter)

			if len(player_list) >= 2:
				menu_state = "main menu"

		elif menu_state == "edit player":
			player_num = pickPlayer(player_list)
			if player_num == None: continue

			used_characters.remove(player_list[player_num].letter)
			new_letter = enterPlayer(player_list, used_characters, player_num)
			player_list[player_num].letter = new_letter
			used_characters.append(new_letter)
			menu_state = "main menu"
		
		elif menu_state == "delete player":
			player_num = pickPlayer(player_list)
			if player_num == None: continue

			used_characters.remove(player_list[player_num].letter)
			player_list.pop(player_num)
			if len(player_list) < 2: menu_state = "add player"
			else: menu_state = "main menu"
	
	return player_list

def main():
	global board

	board_displayer = BoardDisplayer()

	# SETUP BOARD
	properties = createProperties()
	for p in properties: board[p.position] = p

	stations = createStations()
	for s in stations: board[s.position] = s

	utilities = createUtilities()
	for u in utilities: board[u.position] = u

	go = Go()
	jail = Jail()
	free_parking = FreeParking()
	go_to_jail = GoToJail()
	income_tax = TaxPlace("income", 4, 200)
	super_tax = TaxPlace("super", 38, 100)
	for i in [go, jail, free_parking, go_to_jail, income_tax, super_tax]: board[i.position] = i

	player_list = createPlayers()
	#player_list = [Player("a"), Player("b")]
	
	board_displayer.setPlayerList(player_list)
	[player.setBoardDisplayer(board_displayer) for player in player_list]

	community_chests = makeCommunityChests(player_list)
	ccm1 = CommunityChestManager(2, community_chests)
	ccm2 = CommunityChestManager(17, community_chests)
	ccm3 = CommunityChestManager(33, community_chests)
	for ccm in [ccm1, ccm2, ccm3]: board[ccm.position] = ccm
	
	# MAIN GAME LOOP
	while True:
		[player.turn() for player in player_list]
	board_displayer.printBoard()

if __name__ == "__main__":
	main()