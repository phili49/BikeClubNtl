from ListItems import app, db, bike

bikes = [
    {"product_id": "1", "name": "Trek Domane SL7", "Price": "7799", "description": "A performance endurance road bike designed for long rides and rough roads, equipped with carbon frame and electronic shifting.", "imageFileName": "TrekDomaneSL7.jpg"},
    {"product_id": "2", "name": "Specialized S-Works Tarmac", "Price": "12000", "description": "A top-tier road racing bike known for its lightweight carbon frame, designed for speed and agility on the race track.", "imageFileName": "Specialized_S-Works_Tarmac.jpg"},
    {"product_id": "3", "name": "Cannondale Synapse Carbon", "Price": "4500", "description": "A versatile endurance road bike, perfect for long distances, featuring a comfortable design and disc brakes for all-weather control.", "imageFileName": "cannondaleSynapseCarbon.jpg"},
    {"product_id": "4", "name": "Giant Defy Advanced Pro", "Price": "6800", "description": "A lightweight and durable endurance road bike, built with carbon fiber and designed for a smooth and efficient ride on any terrain.", "imageFileName": "giantDefyAdvancedPro.jpg"},
    {"product_id": "5", "name": "Santa Cruz 5010", "Price": "5799", "description": "A trail mountain bike known for its playful handling, featuring 27.5-inch wheels and a lightweight carbon frame for quick and responsive trail riding.", "imageFileName": "santaCruz5010.jpg"},
    {"product_id": "6", "name": "Yeti SB130", "Price": "6200", "description": "A top-rated all-mountain bike with a unique suspension design, offering both climbing efficiency and descending capability.", "imageFileName": "yetiSB130.jpg"}
]
with app.app_context():
    db.create_all()
    
    for b in bikes:
        newBike = bike(product_id = b['product_id'], name = b['name'], price = b['Price'], description = b['description'], imagefilename = b['imageFileName'])
        db.session.add(newBike)
        
    db.session.commit()