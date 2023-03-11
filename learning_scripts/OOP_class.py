class POI():
    def __init__(self, name,phone,website,address,coordinates,categories,business_hours):
        self.name = name
        self.phone = phone
        self.website = website
        self.address = address
        self.coordinates = coordinates
        self.categories = categories
        self.business_hours = business_hours    

listing = POI("NextbillionAI","","nextbillion.ai",'first floor,Trendz utility',"x,y",'Office',"open")

print("name: " + listing.name)
print("phone: " + listing.phone)
print("website: " + listing.website)
print("address: " + listing.address)
print("coordinates: " + listing.coordinates)
print("categories: " + listing.categories)
print("business_hours: " + listing.business_hours)