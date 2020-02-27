import discord
from _thread import start_new_thread
import time
import sys

token = "[token]"
client = discord.Client()

commands = {
	";remove [num]" : "Removes the latest messages in a given channel, stopping at input. Defaults to 5.",
	";assignrole [user] [role]" : "Gives a user a given role.",
	";removerole [user] [role]" : "Removes a given role from a user.",
	";selfrole [role]" : "Assigns a role to the caller. Does not assign roles with moderator permissions.",
	";roles" : "Returns a list of roles.",
	";avatar [user]" : "Returns the avatar for a given user.",
	";votemute [user]" : "Submit a vote to mute a given user. Only trusted users can vote.",
}

votemute = {}
voted = {}
neededtokick = 3
muted = []

pinreaction = "based"
neededtopin = 4


def id_from_ping(inp):
	try:
		return inp.replace("<@!", "").replace("<@", "").replace(">", "")
	except:
		return None

def split_clear_empty(inp, s):
	ret = inp.split(s)
	for v in ret:
		if v == "":
			ret.remove(v)
	return ret 

def role_by_name(name, guild):
	roleto = None
	for role in guild.roles:
		if role.name.lower() == name.lower():
			roleto = role
			break
	return roleto

def member_by_name(name, guild):
	memberto = None
	for member in guild.members:
		if member.name.lower() == name.lower() or str(member.id) == name:
			memberto = member
			break
	return memberto

timeconvert = {
	"s" : 1,
	"m" : 60,
	"h" : 3600,
	"d" : 86400,
	"w" : 604800,
}
def time_from_str(inp):
	try:
		command = inp.split(" ")
		total = 0
		for i in command:
			for s, v in timeconvert.items():
				if i.find(s) != -1:
					mult = int(i.replace(s, ""))
					total = total + (v * mult)
		return total
	except Exception as e:
		print(e)
		return 0

@client.event
async def on_message(message):
	if message.author == client.user:
		return
	
	for tup in muted:
			if tup[2] < time.time():
				print(tup[1])
				await tup[1].remove_roles(tup[0])
				muted.remove(tup)
		
	#log
	tfile = ""
	for a in message.attachments:
		tfile = tfile+" "+a.url
	
	tosend = message.content.replace("@", "[@]") #sanitize pings
	for channel in message.guild.channels:
		if channel.name == "message-logs":
			await channel.send(content=("["+str(message.channel)+"] "+str(message.author)+": "+tosend+" "+tfile))
			break
			
	#auto responses
	if message.content.find("zWsZNdB") != -1:
		await message.delete()
		await message.channel.send("<@!"+str(message.author.id)+"> Stop fucking posting that link")
	
	#commands list
	cn = message.content.split(" ")[0]
	if cn == ";help" or cn == ";commands" or cn == ";cmds":
		tosend = "Current commands:```"
		for i, v in commands.items():
			tosend = tosend+i+" : "+v+"\n"
		tosend = tosend+"```"
		
		await message.channel.send(tosend)
	
	#remove command
	if message.content.split(" ")[0]  == ";remove":
		valid = False
		for role in message.author.roles:
			if role.permissions.manage_messages or role.permissions.administrator:
				valid = True
				break	
		if valid:
			try:
				num = int(message.content.split(" ")[1])
			except: num = 5
			#print("Purging...")
			await message.channel.purge(limit=num)
			await message.channel.send("Cleared "+str(num)+" messages. Called by ``"+message.author.name+"``.")
		else:
			await message.channel.send("You do not have permission to delete messages.")
	
	#assign command
	if message.content.split(" ")[0]  == ";assignrole":
		valid = False
		for role in message.author.roles:
			if role.permissions.manage_roles or role.permissions.administrator:
				valid = True
				break	
		if not valid:
			await message.channel.send("You do not have permission to manage roles.")
			return
			
		cmds = split_clear_empty(message.content, " ")
		if len(cmds) != 3:
			await message.channel.send("Usage is ``;assignrole [member] [role]``. Replace spaces in a role name with underscores.")
			return
			
		user = id_from_ping(cmds[1])
		memberto = member_by_name(user, message.guild)
		
		rolename = cmds[2].replace("_", " ")
		roleto = role_by_name(rolename, message.guild)
		if roleto and memberto:
			try:
				await memberto.add_roles(roleto)
				await message.channel.send("Added role ``"+roleto.name+"``.")
			except:
				await message.channel.send("Failed to assign role.")
		else:
			if not roleto:
				await message.channel.send("Not a valid role.")
			if not memberto:
				await message.channel.send("Not a valid member.")
	
	#removerole command
	if message.content.split(" ")[0] == ";removerole":
		valid = False
		for role in message.author.roles:
			if role.permissions.manage_roles or role.permissions.administrator:
				valid = True
				break	
		if not valid:
			await message.channel.send("You do not have permission to manage roles.")
			return
		
		cmds = split_clear_empty(message.content, " ")
		if len(cmds) != 3:
			await message.channel.send("Usage is ``;removerole [member] [role]``. Replace spaces in a role name with underscores.")
			return
			
		user = id_from_ping(cmds[1])
		memberto = member_by_name(user, message.guild)
		
		rolename = cmds[2].replace("_", " ")
		roleto = role_by_name(rolename, message.guild)
		
		if roleto and memberto:
			try:
				await memberto.remove_roles(roleto)
				await message.channel.send("Removed role ``"+roleto.name+"``.")
			except:
				await message.channel.send("Failed to remove role.")
		else:
			if not roleto:
				await message.channel.send("Not a valid role.")
			if not memberto:
				await message.channel.send("Not a valid member.")
	
	#selfrole command
	if message.content.split(" ")[0] == ";selfrole":
		if len(message.content.split(" ")) != 2:
			await message.channel.send("Usage is ``;selfrole [role]``. Replace spaces in a role name with underscores.")
			return
		
		rolename = message.content.split(" ")[1].replace("_", " ")
		roleto = role_by_name(rolename, message.guild)
		
		if roleto:
			try:
				if roleto.permissions.administrator or roleto.permissions.manage_messages or roleto.permissions.kick_members or roleto.permissions.view_audit_log:
					await message.channel.send("You cannot self-assign a role with moderator permissions.")
				else:
					if roleto in message.author.roles:
						await message.author.remove_roles(roleto)
						await message.channel.send("Removed role ``"+roleto.name+"``.")
					else:
						await message.author.add_roles(roleto)
						await message.channel.send("Added role ``"+roleto.name+"``.")
			except: 
				await message.channel.send("Could not edit role ``"+roleto.name+"``.")
					
		else:
			await message.channel.send("Not a valid role.")
	
	#roles command
	if message.content.split(" ")[0] == ";roles":
		tosend = "Roles in ``"+message.guild.name+"`` \n```"
		for role in message.guild.roles:
			tosend = tosend+"\n"+role.name
		tosend = tosend+"```"
		
		await message.channel.send(tosend)
	
	#avatar command
	if message.content.split(" ")[0] == ";avatar":
		cmds = message.content.split(" ")
		if len(cmds) != 2:
			await message.channel.send("Usage is ``;avatar [user]``")
			return
		
		user = id_from_ping(cmds[1])
		memberto = member_by_name(user, message.guild)
		
		if memberto:
			await message.channel.send("Avatar for ``"+memberto.name+"`` "+str(memberto.avatar_url))
		else:
			await message.channel.send("Not a valid member.")
	
	#mute
	if message.content.split(" ")[0] == ";mute":
		valid = False
		for role in message.author.roles:
			if role.permissions.manage_roles:
				valid = True
				break
		if not valid:
			await message.channel.send("You do not have permission to manage roles.")
			return
		
		name = id_from_ping(message.content.split(" ")[1])
		user = member_by_name(name, message.guild)
		
		if not user:
			await message.channel.send("That is not a valid user.")
			return
			
		seconds = time_from_str(message.content[7+len(name):])
		if seconds != 0:
			roleto = role_by_name("muted", message.guild)
			if not roleto:
				await message.channel.send("Could not find a role named Muted.")
				return
			muted.append((roleto, user, time.time()+seconds))
			await user.add_roles(roleto)
			await message.channel.send("Muted user ``"+str(user)+"`` for "+str(seconds)+" seconds.")
		else:
			await message.channel.send("Not a valid time.")
			return
	
	#unmute
	if message.content.split(" ")[0] == ";unmute":
		valid = False
		for role in message.author.roles:
			if role.permissions.manage_roles:
				valid = True
				break
		if not valid:
			await message.channel.send("You do not have permission to manage roles.")
			return
		
		name = id_from_ping(message.content.split(" ")[1])
		user = member_by_name(name, message.guild)
		if not user:
			await message.channel.send("That is not a valid user.")
			return
		else:
			for tup in muted:
				if tup[1] == user:
					await tup[1].remove_roles(tup[0])
					await message.channel.send("Unmuted user ``"+str(user)+"``.")
					muted.remove(tup)
					break
		
	#votemute
	if message.content.split(" ")[0] == ";votemute":
		cmds = split_clear_empty(message.content, " ")
		valid = False
		for role in message.author.roles:
			if role.name.lower() == "trusted":
				valid = True
				break
				
		if not valid:
			await message.channel.send("Only trusted users are allowed to use ;votemute")
			return
		if len(cmds) != 2:
			await message.channel.send("Usage is ``;votemute [user]``.")
			return
		
		user = id_from_ping(cmds[1])
		memberto = member_by_name(user, message.guild)
		
		roleto = None
		for role in message.guild.roles:
			if role.name.lower() == "muted":
				roleto = role
				break
		
		if memberto and roleto:
			added = False
			for i, v in voted.items():
				if i == message.author.id:
					added = True
					if not memberto.id in v:
						v.append(memberto.id)
					else:
						await message.channel.send("You have already voted on user ``"+memberto.name+"``.")
						return
			if not added:
				voted[message.author.id] = []
				voted[message.author.id].append(memberto.id)
			
			added = False
			for i, v in votemute.items():
				if i == memberto.id:
					added = True
					votemute[memberto.id] = (votemute.get(memberto.id) + 1)
					await message.channel.send(str(votemute.get(memberto.id))+" votes received.")
					if votemute.get(memberto.id) == neededtokick:
						await memberto.add_roles(roleto)
						await message.channel.send("Muted user ``"+memberto.name+"``.")
						
			if added == False:
				await message.channel.send("1 vote received.")
				votemute[memberto.id] = 1
		else:
			if not memberto:
				await message.channel.send("Not a valid member.")
			if not roleto:
				await message.channel.send("Could not find a role named Muted.")

@client.event
async def on_raw_reaction_add(payload):
	reaction = payload.emoji
	user = client.get_user(payload.user_id)
	channel = client.get_channel(payload.channel_id)
	message = await channel.fetch_message(payload.message_id)
	if message.author == client.user or str(payload.message_id) in open("pinned.txt","r").read().split("\n"):
		return
		
	if reaction.name == pinreaction:
		channelto = None
		for echannel in message.guild.channels:
			if echannel.name == "archives-of-based":
				channelto = echannel
		if not channelto:
			print("No archive channel found.")
			return
	
	for exreaction in message.reactions:
		if exreaction.emoji.name == pinreaction:
			if exreaction.count > (neededtopin - 1):
				open("pinned.txt","a").write(str(message.id)+"\n")
				tfile = ""
				for a in message.attachments:
					tfile = tfile+" "+a.url
				await channelto.send(message.author.name+" in #"+channel.name+":\n"+message.content.replace("@","[@]")+tfile)
	
	
	

	
@client.event
async def on_ready():
	print("Running...")




client.run(token)