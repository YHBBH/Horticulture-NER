# -*- coding: utf-8 -*-
# @Author: Jie Yang
# @Date:   2017-09-14 16:38:21
# @Last Modified by:   Jie Yang,     Contact: jieynlp@gmail.com
# @Last Modified time: 2018-05-01 21:17:27

import re

def maximum_matching(train_text, decode_text, f,entityRe = r'\[\@.*?\#.*?\*\](?!\#)', recommendRe = r'\[\$.*?\#.*?\*\](?!\#)'):
	# print("Training data:")
	# print(train_text)
	# print("Decode data:")
	# print(decode_text)
	# train_text = train_text.decode('utf-8')
	# decode_text = decode_text.decode('utf-8')

	extracted_dict = {}
	max_length = 0

	for match in re.finditer(entityRe, train_text):
		recognized_entity = train_text[match.span()[0]:match.span()[1]]
		[entity, entity_type] = recognized_entity.strip('[@]*').rsplit('#',1)
		
		if len(entity) > max_length:
			max_length = len(entity)

#标注的词传入词典
		extracted_dict[entity] = entity_type
		#print("dict:", extracted_dict)
		# with open(f, 'a+', encoding='utf-8', ) as f:
		# 	s = str(recognized_entity)
		# 	f.writelines('\n'+s)
		# 	f.close()

	with open(f, 'r+', encoding='utf-8') as f:
		while 1:
			line = f.readline()
			if len(line) == 0:
				break
			for match in re.finditer(entityRe, line):
				recognized_entity = line[match.span()[0]:match.span()[1]]
				[entity, entity_type] = recognized_entity.strip('[@]*').rsplit('#', 1)

				if len(entity) > max_length:
					max_length = len(entity)

		# 标注的词传入词典
				extracted_dict[entity] = entity_type
				#f.writelines(recognized_entity)
				#print("dict:", extracted_dict)



	if len(extracted_dict) == 0:
		train_text = str(train_text)
		decode_text = str(decode_text)
		return train_text + decode_text

	## only recommend following 10 sentences (reduce time)
	near_sentences = ""
	far_sentences = ""
	sentences = decode_text.split('\n')
	for idx in range(len(sentences)):
		if idx != len(sentences) -1 :
			new_string = sentences[idx] + '\n'
		else:
			new_string = sentences[idx]
		if idx > 20 :
			far_sentences += new_string
		else:
			near_sentences += new_string
	decode_text = near_sentences



	### forward maximum match algorithm with following conditions:
	### 1. for previous recommend entities, remove them and recommend again
	### 2. for recognized entities, ignored them (forward process ends at the begining of recognized entity)
	
	## remove previous recommend entity format
	decode_no_recommend = ""
	last_entity_end = 0
	newDecode_text = train_text + decode_text
	# print(newDecode_text)
	# print('--------------')
	for match in re.finditer(recommendRe, newDecode_text):
		decode_no_recommend += newDecode_text[last_entity_end:match.span()[0]]
		recommend_entity = newDecode_text[match.span()[0]:match.span()[1]]
		entity = recommend_entity.strip('[$]').rsplit('#',1)[0]
		decode_no_recommend += entity
		last_entity_end = match.span()[1]
	decode_no_recommend += newDecode_text[last_entity_end:]
	# print(decode_no_recommend)
	## ignored annotated entities but record them position (in entity_recognized_list)
	decode_origin = ""
	entity_recognized_list = []
	last_entity_end = 0
	for match in re.finditer(entityRe, decode_no_recommend):
		decode_origin += decode_no_recommend[last_entity_end:match.span()[0]]
		entity_recognized_list += [0]*(match.span()[0]-last_entity_end)
		recommend_entity = decode_no_recommend[match.span()[0]:match.span()[1]]
		[entity, recognized_type] = recommend_entity.strip('[@]*').rsplit('#',1)
		decode_origin += entity
		entity_recognized_list += ["B-@-"+recognized_type] +["I-@-"+recognized_type] *(len(entity)-1)
		last_entity_end = match.span()[1]
	decode_origin += decode_no_recommend[last_entity_end:]
	entity_recognized_list += [0]*(len(decode_no_recommend)-last_entity_end)
	assert(len(decode_origin) == len(entity_recognized_list))
	# print(decode_origin)
	# print(entity_recognized_list)

	## forward maximum matching (FMM)
	origin_length = len(decode_origin)
	FMM_start = 0 
	FMM_end = (FMM_start + max_length) if (FMM_start + max_length) < origin_length-1 else origin_length-1
	entity_recommend_list = []
	while FMM_start < origin_length:

		if FMM_end == FMM_start:
			entity_recommend_list += [0]
			FMM_start += 1
			FMM_end = (FMM_start + max_length) if (FMM_start + max_length) < origin_length-1 else origin_length-1
		## recognized span detection: for the following two conditions, it jump when the word is located in recognized entity span
		elif entity_recognized_list[FMM_start] != 0 or decode_origin[FMM_start] == '\n':
			entity_recommend_list += [0]
			FMM_start += 1
			FMM_end = (FMM_start + max_length) if (FMM_start + max_length) < origin_length-1 else origin_length-1
		elif entity_recognized_list[FMM_end] != 0 or decode_origin[FMM_end] == '\n':
			FMM_end -= 1
		## finish recognized span detection	
		else:
			word = decode_origin[FMM_start:FMM_end]
			if word in extracted_dict:
				entity_recommend_list += ["B-$-"+extracted_dict[word]] +["I-$-"+extracted_dict[word]] *(FMM_end-FMM_start-1)
				FMM_start = FMM_end
				FMM_end = (FMM_start + max_length) if (FMM_start + max_length) < origin_length-1 else origin_length-1
			else:
				FMM_end -= 1
	# print(entity_recommend_list)
	assert(len(entity_recommend_list)== len(entity_recognized_list))
	recommend_decode_text =  merge_text_with_entity(decode_origin, entity_recognized_list, entity_recommend_list)
	return recommend_decode_text + far_sentences

def generateDictFile(f1, train_text):
    f = open(f1,"a+",encoding="utf-8")
    f.seek(0)
    lst = []
    for line in f.readlines():
        line1 = line.split("\n")
        lst.append(line1[0])

    entityRe = r'\[\@.*?\#.*?\*\](?!\#)'
    for match in re.finditer(entityRe, train_text):
        recognized_entity = train_text[match.span()[0]:match.span()[1]]
        if recognized_entity not in lst:
            #print(recognized_entity)
            f.writelines('\n' + recognized_entity+'\n')

def DictFilerRank(f1,train_text):
    results = []
    f = open(f1, "r+",encoding="utf-8")
    lines = f.readlines()
    lines.sort(key=lambda x: len(x), reverse=True)
    for line in lines:
        results.append(line)
    f.close()

    f = open(f1, "w",encoding="utf-8")
    for result in results:
        # print(line)
        f.writelines(result)
    f.close()

def merge_text_with_entity(origin_text, recognized_list, recommend_list):
	length = len(origin_text)
	assert(len(recognized_list)==length)
	assert(len(recommend_list)==length)
	combine_list = recommend_list
	for idx in range(length):
		if combine_list[idx] == 0 and recognized_list[idx] != 0:
			combine_list[idx] = recognized_list[idx]
	new_string = ""
	entity_string = ""
	entity_type = "Error"
	entity_source = "Error"
	for idx in range(length):
		if combine_list[idx] == 0:
			if entity_string:
				new_string += "["+entity_source + entity_string + "#" + entity_type+"*]"
				entity_string = ""
				entity_type = "Error"
				entity_source = "Error"
			# print(new_string)
			new_string += origin_text[idx]

		elif combine_list[idx].startswith("B-"):
			if entity_string:
				new_string += "["+entity_source + entity_string + "#" + entity_type+"*]"
				entity_string = ""
				entity_type = "Error"
				entity_source = "Error"
			entity_string = origin_text[idx]
			entity_type = combine_list[idx][4:]
			entity_source = combine_list[idx][2:3]
		elif combine_list[idx].startswith("I-"):
			entity_string += origin_text[idx]
		else:
			print("merge_text_with_entity error!")
	if entity_string:
		new_string += "["+entity_source + entity_string + "#" + entity_type +"*]"
		entity_string = ""
		entity_type = "Error"
		entity_source = "Error"
	return new_string




if __name__ == '__main__':
	train_text = "于是朱物华我就给[@朱物华#Location*]校长、[@张钟俊#Location*]院长给他们写了一个报告!"
	decode_text = "张钟俊院长，给他[$张钟俊#Location*]and[$张钟俊#Location*]..[@朱物华#Location*]aircraft,weekend."
	print(train_text)
	#f1 = "C:\\Users\\dell\\Desktop\\plant.txt"
	print(maximum_matching(train_text,decode_text,'plant.txt'))
	print(generateDictFile('plant.txt',train_text))
	#print(extracted_dict[0])
	DictFilerRank('plant.txt',train_text)