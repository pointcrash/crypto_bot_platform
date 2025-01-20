from slugify import slugify

string = 'how to create a portal'
string_ru = 'как МНе создать портал?!!'

slug = slugify(string)
slug_ru = slugify(string_ru)
print(slug)
print(slug_ru)
