import pandas as pd
import random
import numpy as np
import json
import os

class WardrobeItem:
    def __init__(self, item_id, category, color, style, season, formality, attributes=None, sales_data=None):
        self.item_id = item_id
        self.category = category.lower()
        self.color = color.lower()
        self.style = style.lower()
        self.season = season.lower()
        self.formality = formality.lower()
        self.attributes = attributes or {}
        self.sales_data = sales_data or {}
    
    def __str__(self):
        base_str = f"{self.color} {self.style} {self.category} ({self.formality}, {self.season})"
        attr_str = ""
        if self.attributes:
            important_attrs = ["pattern", "material", "fit"]
            attr_parts = [f"{attr}: {self.attributes.get(attr)}" for attr in important_attrs if attr in self.attributes]
            if attr_parts:
                attr_str = f" - {', '.join(attr_parts)}"
        
        popularity = ""
        if self.attributes and "popularity" in self.attributes:
            popularity = f" [{self.attributes['popularity']}]"
            
        return base_str + attr_str + popularity

class Wardrobe:
    def __init__(self):
        self.items = []
        self.categories = set()
        
    def add_item(self, item):
        self.items.append(item)
        self.categories.add(item.category)
        
    def get_items_by_category(self, category):
        return [item for item in self.items if item.category == category.lower()]
    
    def get_all_categories(self):
        return list(self.categories)

class OutfitRecommender:
    def __init__(self, wardrobe):
        self.wardrobe = wardrobe
        
        # Compatibility rules
        self.color_matches = {
            'white': ['black', 'blue', 'red', 'green', 'brown', 'grey', 'navy', 'beige'],
            'black': ['white', 'red', 'grey', 'silver', 'gold', 'pink', 'purple'],
            'blue': ['white', 'grey', 'brown', 'navy', 'red', 'beige'],
            'red': ['white', 'black', 'blue', 'grey', 'brown'],
            'green': ['white', 'beige', 'brown', 'grey', 'black'],
            'brown': ['white', 'blue', 'green', 'beige', 'grey'],
            'grey': ['white', 'black', 'blue', 'red', 'pink', 'purple'],
            'navy': ['white', 'blue', 'grey', 'red'],
            'beige': ['white', 'blue', 'green', 'brown', 'navy', 'black'],
            'pink': ['black', 'grey', 'navy', 'white'],
            'purple': ['white', 'black', 'grey'],
            'yellow': ['white', 'blue', 'grey', 'navy'],
            'orange': ['white', 'blue', 'navy', 'grey'],
        }
        
        self.style_matches = {
            'casual': ['casual', 'sporty', 'streetwear'],
            'formal': ['formal', 'business'],
            'business': ['formal', 'business', 'semi-formal'],
            'sporty': ['casual', 'sporty', 'streetwear'],
            'streetwear': ['casual', 'sporty', 'streetwear'],
            'semi-formal': ['semi-formal', 'business', 'formal'],
            'vintage': ['vintage', 'casual', 'formal'],
            'bohemian': ['bohemian', 'casual'],
            'preppy': ['preppy', 'casual', 'semi-formal'],
        }
        
        self.formality_matches = {
            'formal': ['formal', 'semi-formal'],
            'semi-formal': ['formal', 'semi-formal', 'casual'],
            'casual': ['casual', 'semi-formal'],
        }
        
        # Weights for recommendations
        self.popularity_weight = 0.6
        self.rating_weight = 0.3
        self.purchase_weight = 0.1
    
    def are_compatible(self, item1, item2):
        """Check if two items are compatible based on color, style, and formality"""
        return (self._are_colors_compatible(item1.color, item2.color) and
                self._are_styles_compatible(item1.style, item2.style) and
                self._are_formalities_compatible(item1.formality, item2.formality))
    
    def _are_colors_compatible(self, color1, color2):
        if color1 == color2:
            return True
        return (color1 in self.color_matches and color2 in self.color_matches[color1]) or \
               (color2 in self.color_matches and color1 in self.color_matches[color2])
    
    def _are_styles_compatible(self, style1, style2):
        if style1 == style2:
            return True
        return (style1 in self.style_matches and style2 in self.style_matches[style1]) or \
               (style2 in self.style_matches and style1 in self.style_matches[style2])
    
    def _are_formalities_compatible(self, formality1, formality2):
        if formality1 == formality2:
            return True
        return (formality1 in self.formality_matches and formality2 in self.formality_matches[formality1]) or \
               (formality2 in self.formality_matches and formality1 in self.formality_matches[formality2])
    
    def _is_season_appropriate(self, item, target_season):
        return item.season == 'all-season' or item.season == target_season
    
    def generate_outfit(self, occasion=None, season='summer'):
        # Define required categories for a complete outfit
        required_categories = ['shirt', 'pants', 'shoes']
        
        # Filter items by season
        season_items = [item for item in self.wardrobe.items 
                        if self._is_season_appropriate(item, season)]
        
        if not season_items:
            return None, "No items suitable for this season."
        
        # Check if we have all required categories
        available_categories = set(item.category for item in season_items)
        missing_categories = [cat for cat in required_categories if cat not in available_categories]
        if missing_categories:
            return None, f"Missing required categories: {', '.join(missing_categories)}"
        
        # Start with a shirt
        shirts = [item for item in season_items if item.category == 'shirt']
        if not shirts:
            return None, "No shirts available for this season."
        
        # Select a shirt with preference for popular items
        base_item = self._select_item_with_popularity(shirts)
        outfit = [base_item]
        
        # Add pants that match the shirt
        pants = [item for item in season_items if item.category == 'pants']
        compatible_pants = [pant for pant in pants if self.are_compatible(base_item, pant)]
        
        if not compatible_pants:
            return None, "No compatible pants found."
        
        selected_pants = self._select_item_with_popularity(compatible_pants)
        outfit.append(selected_pants)
        
        # Add shoes that match both shirt and pants
        shoes = [item for item in season_items if item.category == 'shoes']
        compatible_shoes = [shoe for shoe in shoes 
                           if self.are_compatible(base_item, shoe) and 
                              self.are_compatible(selected_pants, shoe)]
        
        if not compatible_shoes:
            return None, "No compatible shoes found."
        
        selected_shoes = self._select_item_with_popularity(compatible_shoes)
        outfit.append(selected_shoes)
        
        # Determine the outfit description
        outfit_style = base_item.style
        outfit_formality = base_item.formality
        description = f"{outfit_formality.capitalize()} {outfit_style} outfit for {season}"
        
        return outfit, description
    
    def _select_item_with_popularity(self, items):
        """Select an item with preference for popular items"""
        if not items:
            return None
            
        # Calculate popularity scores
        items_with_scores = []
        for item in items:
            score = random.random()  # Base randomness
            
            # Add popularity from attributes
            if item.attributes and "popularity" in item.attributes:
                pop = item.attributes["popularity"]
                if pop == "high":
                    score += 0.3 * self.popularity_weight
                elif pop == "medium":
                    score += 0.2 * self.popularity_weight
                elif pop == "trending":
                    score += 0.4 * self.popularity_weight
            
            # Add score from sales data
            if item.sales_data:
                if "rating" in item.sales_data:
                    try:
                        score += float(item.sales_data["rating"]) * 0.1 * self.rating_weight
                    except (ValueError, TypeError):
                        pass
                
                if "purchases" in item.sales_data:
                    try:
                        score += min(float(item.sales_data["purchases"]) / 100, 0.5) * self.purchase_weight
                    except (ValueError, TypeError):
                        pass
            
            items_with_scores.append((item, score))
        
        # Sort by score and select from top 3 (or fewer if less available)
        items_with_scores.sort(key=lambda x: x[1], reverse=True)
        top_n = min(3, len(items_with_scores))
        return random.choice([item for item, _ in items_with_scores[:top_n]])

class FashionStylist:
    def __init__(self):
        self.wardrobe = Wardrobe()
        self.recommender = OutfitRecommender(self.wardrobe)
        self.dresses_dataset_path = os.path.join(os.path.expanduser("~"), "Downloads", "Dresses_Attribute_Sales.csv")
        self.dataset_path = "fashion_dataset.json"
        
        # Try to load the dresses dataset first, then fall back to other options
        if os.path.exists(self.dresses_dataset_path):
            self.load_dresses_dataset()
        elif os.path.exists(self.dataset_path):
            self.load_dataset()
        else:
            self.create_simulated_dataset()
            self.load_dataset()
    
    def create_simulated_dataset(self):
        """Create a simulated fashion dataset with various attributes and sales data"""
        categories = ["shirt", "pants", "shoes", "dress", "jacket", "skirt"]
        colors = ["white", "black", "blue", "red", "green", "brown", "grey", "navy", "beige", "pink"]
        styles = ["casual", "formal", "business", "sporty", "streetwear", "vintage", "bohemian"]
        seasons = ["summer", "winter", "spring", "fall", "all-season"]
        formalities = ["formal", "semi-formal", "casual"]
        
        # Additional attributes
        patterns = ["solid", "striped", "floral", "plaid", "polka dot", "checkered"]
        materials = ["cotton", "silk", "wool", "polyester", "linen", "denim", "leather"]
        fits = ["slim", "regular", "loose", "oversized", "fitted"]
        popularity_levels = ["low", "medium", "high", "trending"]
        
        # Generate items
        items = []
        for i in range(1, 51):  # Generate 50 items
            category = random.choice(categories)
            color = random.choice(colors)
            style = random.choice(styles)
            season = random.choice(seasons)
            formality = random.choice(formalities)
            
            # Generate attributes
            attributes = {
                "pattern": random.choice(patterns),
                "material": random.choice(materials),
                "fit": random.choice(fits),
                "popularity": random.choice(popularity_levels)
            }
            
            # Generate sales data
            sales_data = {
                "rating": round(random.uniform(1.0, 5.0), 1),
                "reviews": random.randint(0, 500),
                "purchases": random.randint(0, 1000),
                "views": random.randint(100, 10000),
                "likes": random.randint(0, 500)
            }
            
            items.append({
                "item_id": i,
                "category": category,
                "color": color,
                "style": style,
                "season": season,
                "formality": formality,
                "attributes": attributes,
                "sales_data": sales_data
            })
        
        # Save to JSON file
        with open(self.dataset_path, 'w') as f:
            json.dump({"items": items}, f, indent=2)
        
        print(f"Created simulated dataset with {len(items)} items")
    
    def load_dresses_dataset(self):
        """Load the Dresses_Attribute_Sales dataset"""
        try:
            df = pd.read_csv(self.dresses_dataset_path)
            item_id = 1
            
            for _, row in df.iterrows():
                # Basic attributes
                category = "dress"
                
                # These are examples and should be adjusted based on actual column names
                color = row.get('Color', 'unknown')
                style = row.get('Style', 'casual')
                season = row.get('Season', 'all-season')
                formality = row.get('Formality', 'casual')
                
                # Additional attributes
                attributes = {}
                attribute_columns = [
                    'Pattern', 'Material', 'Sleeve_Length', 'Neckline', 'Fit', 
                    'Length', 'Price_Range'
                ]
                
                for attr in attribute_columns:
                    if attr in row and not pd.isna(row[attr]):
                        attributes[attr.lower()] = str(row[attr])
                
                # Sales data
                sales_data = {}
                sales_columns = [
                    'Rating', 'Reviews', 'Sales', 'Views', 'Likes'
                ]
                
                for col in sales_columns:
                    if col in row and not pd.isna(row[col]):
                        sales_data[col.lower()] = row[col]
                
                # Create and add the wardrobe item
                item = WardrobeItem(
                    item_id,
                    category,
                    color,
                    style,
                    season,
                    formality,
                    attributes,
                    sales_data
                )
                self.wardrobe.add_item(item)
                item_id += 1
                
            print(f"Added {item_id-1} dresses to the wardrobe from Dresses_Attribute_Sales dataset")
            
        except Exception as e:
            print(f"Error loading Dresses_Attribute_Sales dataset: {e}")
            print("Falling back to simulated dataset")
            self.create_simulated_dataset()
            self.load_dataset()
    
    def load_dataset(self):
        """Load the fashion dataset and populate the wardrobe"""
        try:
            with open(self.dataset_path, 'r') as f:
                data = json.load(f)
                
            # Add items to wardrobe
            for item_data in data["items"]:
                item = WardrobeItem(
                    item_data["item_id"],
                    item_data["category"],
                    item_data["color"],
                    item_data["style"],
                    item_data["season"],
                    item_data["formality"],
                    item_data.get("attributes", {}),
                    item_data.get("sales_data", {})
                )
                self.wardrobe.add_item(item)
                
            print(f"Loaded {len(data['items'])} items from the fashion dataset")
        except Exception as e:
            print(f"Error loading dataset: {e}")
            print("Creating sample wardrobe")
            self.initialize_sample_wardrobe()
    
    def initialize_sample_wardrobe(self):
        """Initialize a sample wardrobe with basic items"""
        # Add sample shirts
        self.wardrobe.add_item(WardrobeItem(1, "shirt", "white", "casual", "all-season", "casual"))
        self.wardrobe.add_item(WardrobeItem(2, "shirt", "blue", "formal", "all-season", "formal"))
        self.wardrobe.add_item(WardrobeItem(3, "shirt", "black", "casual", "all-season", "casual"))
        self.wardrobe.add_item(WardrobeItem(4, "shirt", "red", "sporty", "summer", "casual"))
        
        # Add sample pants
        self.wardrobe.add_item(WardrobeItem(5, "pants", "blue", "casual", "all-season", "casual"))
        self.wardrobe.add_item(WardrobeItem(6, "pants", "black", "formal", "all-season", "formal"))
        self.wardrobe.add_item(WardrobeItem(7, "pants", "beige", "casual", "summer", "casual"))
        self.wardrobe.add_item(WardrobeItem(8, "pants", "grey", "formal", "all-season", "formal"))
        
        # Add sample shoes
        self.wardrobe.add_item(WardrobeItem(9, "shoes", "white", "casual", "all-season", "casual"))
        self.wardrobe.add_item(WardrobeItem(10, "shoes", "black", "formal", "all-season", "formal"))
        self.wardrobe.add_item(WardrobeItem(11, "shoes", "brown", "casual", "all-season", "semi-formal"))
        self.wardrobe.add_item(WardrobeItem(12, "shoes", "blue", "sporty", "summer", "casual"))
    
    def add_item_to_wardrobe(self, category, color, style, season, formality, attributes=None, sales_data=None):
        item_id = len(self.wardrobe.items) + 1
        new_item = WardrobeItem(item_id, category, color, style, season, formality, attributes, sales_data)
        self.wardrobe.add_item(new_item)
        return new_item
    
    def get_outfit_recommendations(self, occasion=None, season='summer', count=2):
        recommendations = []
        messages = []
        
        # Try to generate the requested number of outfits
        attempts = 0
        max_attempts = count * 3  # Allow more attempts than requested outfits
        
        while len(recommendations) < count and attempts < max_attempts:
            outfit, message = self.recommender.generate_outfit(occasion, season)
            if outfit:
                recommendations.append((outfit, message))
            else:
                messages.append(message)
            attempts += 1
        
        # If we couldn't generate enough outfits, add the error messages
        if not recommendations:
            return None, messages
        
        return recommendations, messages

def display_outfit(outfit, description):
    print(f"\n{description}:")
    for item in outfit:
        print(f"- {item}")

def main():
    stylist = FashionStylist()
    
    print("Welcome to the AI Fashion Stylist!")
    print("==================================")
    print("Enhanced with Dresses_Attribute_Sales Dataset")
    
    while True:
        print("\nOptions:")
        print("1. View my wardrobe")
        print("2. Add item to wardrobe")
        print("3. Get outfit recommendations")
        print("4. View popular items")
        print("5. Search by attribute")
        print("6. Exit")
        
        choice = input("\nEnter your choice (1-6): ")
        
        if choice == '1':
            print("\nYour Wardrobe:")
            categories = stylist.wardrobe.get_all_categories()
            for category in categories:
                print(f"\n{category.capitalize()}s:")
                items = stylist.wardrobe.get_items_by_category(category)
                for item in items:
                    print(f"- {item}")
        
        elif choice == '2':
            category = input("Enter category (shirt, pants, shoes, dress, etc.): ").lower()
            color = input("Enter color: ").lower()
            style = input("Enter style (casual, formal, sporty, etc.): ").lower()
            season = input("Enter season (summer, winter, all-season, etc.): ").lower()
            formality = input("Enter formality (formal, semi-formal, casual): ").lower()
            
            # Additional attributes
            print("\nAdditional attributes (press Enter to skip):")
            pattern = input("Pattern (e.g., solid, floral, striped): ").lower()
            material = input("Material (e.g., cotton, silk, wool): ").lower()
            fit = input("Fit (e.g., slim, regular, loose): ").lower()
            
            attributes = {}
            if pattern:
                attributes["pattern"] = pattern
            if material:
                attributes["material"] = material
            if fit:
                attributes["fit"] = fit
            
            new_item = stylist.add_item_to_wardrobe(category, color, style, season, formality, attributes)
            print(f"\nAdded to wardrobe: {new_item}")
        
        elif choice == '3':
            season = input("Enter season (summer, winter, spring, fall): ").lower()
            recommendations, messages = stylist.get_outfit_recommendations(season=season, count=2)
            
            if recommendations:
                print("\nRecommended Outfits:")
                for i, (outfit, description) in enumerate(recommendations, 1):
                    print(f"\nOutfit {i}: {description}")
                    for item in outfit:
                        print(f"- {item}")
            else:
                print("\nCouldn't generate recommendations:")
                for message in messages:
                    print(f"- {message}")
        
        elif choice == '4':
            # View popular items based on sales data and attributes
            print("\nPopular Items in Your Wardrobe:")
            
            # Get all items and sort by popularity metrics
            items = stylist.wardrobe.items
            items_with_popularity = []
            
            for item in items:
                popularity_score = 0
                
                # Check attributes for popularity
                if item.attributes and "popularity" in item.attributes:
                    if item.attributes["popularity"] == "high":
                        popularity_score += 3
                    elif item.attributes["popularity"] == "medium":
                        popularity_score += 2
                    elif item.attributes["popularity"] == "trending":
                        popularity_score += 4
                
                # Check sales data
                if item.sales_data:
                    if "rating" in item.sales_data:
                        try:
                            popularity_score += float(item.sales_data["rating"]) * 0.5
                        except (ValueError, TypeError):
                            pass
                    
                    if "purchases" in item.sales_data:
                        try:
                            popularity_score += min(float(item.sales_data["purchases"]) / 100, 5)
                        except (ValueError, TypeError):
                            pass
                            
                    if "reviews" in item.sales_data:
                        try:
                            popularity_score += min(float(item.sales_data["reviews"]) / 50, 3)
                        except (ValueError, TypeError):
                            pass
                
                items_with_popularity.append((item, popularity_score))
            
            # Sort by popularity score (higher is better)
            items_with_popularity.sort(key=lambda x: x[1], reverse=True)
            
            # Display top 10 items or all if less than 10
            top_items = items_with_popularity[:min(10, len(items_with_popularity))]
            
            if top_items:
                for i, (item, score) in enumerate(top_items, 1):
                    print(f"{i}. {item} - Popularity Score: {score:.1f}")
            else:
                print("No items found with popularity data.")
        
        elif choice == '5':
            # Search by attribute
            print("\nSearch Items by Attribute:")
            print("Available attributes: color, style, season, formality, pattern, material, fit")
            
            attribute = input("Enter attribute name: ").lower()
            value = input("Enter attribute value: ").lower()
            
            matching_items = []
            for item in stylist.wardrobe.items:
                # Check basic attributes
                if attribute in ["color", "style", "season", "formality", "category"]:
                    if getattr(item, attribute, "").lower() == value:
                        matching_items.append(item)
                # Check additional attributes dictionary
                elif item.attributes and attribute in item.attributes:
                    if item.attributes[attribute].lower() == value:
                        matching_items.append(item)
            
            if matching_items:
                print(f"\nFound {len(matching_items)} items matching {attribute}={value}:")
                for i, item in enumerate(matching_items, 1):
                    print(f"{i}. {item}")
            else:
                print(f"No items found with {attribute}={value}")
        
        elif choice == '6':
            print("\nThank you for using the AI Fashion Stylist!")
            break
        
        else:
            print("\nInvalid choice. Please try again.")

if __name__ == "__main__":
    main()