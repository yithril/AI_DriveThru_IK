# Bug Tracking Document

## Current Status: Voice AI Drive-Thru System

**Last Updated:** January 15, 2025  
**System Version:** Development/Demo - Major Bugs Resolved!

---

## 🎯 Working Features

✅ **Add single item** - Successfully adds one item to order  
✅ **Add multiple items** - Can add multiple items in one utterance  
✅ **Add items with modifications** - Can add items with customizations (e.g., "quantum burger with no onions")  
✅ **Remove items** - Can remove items from order  
✅ **Modify items** - Can modify existing items (quantity, size, ingredients)  
✅ **Answer questions** - Responds to customer questions about menu/restaurant  
✅ **Order total** - Provides total when customer wants to finish  
✅ **Clear order** - Can clear out entire order  
✅ **Validation** - Guards against too many items (MAX_TOTAL_ITEMS = 20)  
✅ **Performance logging** - Tracks timing for each step  
✅ **"Anything else?" prompt** - Asks follow-up question after adding items  

---

## Outstanding Issues


#### **BUG-008: Error Messages Exposed to Customers**
- **Description:** When system errors occur, technical error messages are shown to customers instead of gentle fallback greetings
- **Expected:** System should fall back to standard gentle greeting on errors
- **Actual:** Technical error messages are exposed to customers
- **Impact:** Medium - Poor UX, jarring customer experience
- **Status:**  Open


#### **BUG-012: Impossible Modifications Not Handled**
- **Description:** System doesn't gracefully handle requests for non-existent ingredients or impossible modifications
- **Example:** "I want a neon burger with two hockey sticks please" - hockey sticks don't exist as an ingredient
- **Expected:** System should politely inform customer that ingredient doesn't exist and suggest alternatives
- **Actual:** Unknown behavior - may fail silently or give confusing error
- **Impact:** Medium - Customer confusion, poor UX
- **Status:**  Open
- **Plan Needed:**
  - Define validation rules for ingredient existence
  - Create friendly error messages for impossible requests
  - Suggest similar/available ingredients as alternatives
  - Handle gracefully without breaking the order flow

#### **BUG-013: Modify Quantity of Non-Existent Order Item**
- **Description:** System incorrectly processes quantity modifications for items not in the current order
- **Example:** "I'd like 5 astro nuggets instead of 3" when astro nuggets isn't on the order
- **Expected:** System should clarify which item to modify or ask if they want to add astro nuggets
- **Actual:** System processes the modification as if the item exists in the order
- **Impact:** Medium - Customer confusion, incorrect order processing
- **Status:**  Open
- **Plan Needed:**
  - Validate that target item exists in current order before modification
  - Handle "instead of" phrasing for non-existent items
  - Clarify intent: modify existing item vs. add new item
  - Provide clear error messages for impossible modifications

#### **BUG-014: Ingredient Additional Costs Not Applied to Order Total** ✅ **RESOLVED**
- **Description:** When customers add extra ingredients (like "extra cheese"), the additional cost is not included in the order total
- **Example:** Customer orders "quantum burger with extra cheese" - cheese has additional_cost of $0.50 but total only shows burger price
- **Expected:** Order total should include base item price + additional costs for extra ingredients
- **Actual:** Only base menu item price is calculated, ignoring MenuItemIngredient.additional_cost values
- **Impact:** High - Restaurant loses money on premium ingredient orders
- **Status:** ✅ **RESOLVED**
- **Solution Implemented:**
  - ✅ Modified `_recalculate_order_totals()` in OrderSessionService to include modifier costs
  - ✅ Added `_calculate_modifier_costs()` method to look up MenuItemIngredient records
  - ✅ Added logic to sum additional_cost values for "extra" type modifications
  - ✅ Added modifier costs to base item price before calculating total
  - ✅ Added comprehensive unit tests for modifier cost calculation
  - ✅ Tested with various ingredient modifications to ensure accuracy

#### **BUG-015: Duplicate Order Items Not Consolidated**
- **Description:** When customers order the same item multiple times (e.g., "2 quantum burgers"), they appear as separate line items instead of being consolidated with quantity
- **Example:** Customer says "I'll take 2 quantum burgers" → shows as 2 separate "Quantum Burger" entries instead of 1 entry with quantity 2
- **Expected:** Identical items should be consolidated into single line items with combined quantity
- **Actual:** Each item addition creates a separate line item
- **Impact:** Medium - Cluttered order display, confusing for customers
- **Status:** 🔄 **PENDING**
- **Plan Needed:**
  - Backend: Add item consolidation logic to group identical items (same menu_item_id + modifications)
  - Frontend: Display consolidated items with quantity
  - Consider: Should consolidation happen in backend or frontend?

#### **BUG-016: AI Response Missing Item Modifications**
- **Description:** When AI confirms adding items, it doesn't mention the modifications (e.g., "extra cheese")
- **Example:** Customer says "quantum burger with extra cheese" → AI responds "Added Quantum Cheeseburger" (missing "with extra cheese")
- **Expected:** AI should mention modifications in confirmation: "Added Quantum Cheeseburger with extra cheese"
- **Actual:** AI only mentions base item name, ignoring customizations
- **Impact:** Medium - Poor user experience, customers can't verify their modifications were understood
- **Status:** 🔄 **PENDING**
- **Plan Needed:**
  - Update AI response generation to include modification details
  - Ensure modifications are passed to response generation
  - Test with various modification types

#### **BUG-017: Order Completion Not Saving to Database**
- **Description:** When customers complete their order, the order is not being archived/saved to PostgreSQL
- **Example:** Customer completes order → order disappears instead of being saved for records
- **Expected:** Completed orders should be saved to database for reporting and records
- **Actual:** Orders are not persisting after completion
- **Impact:** High - No order history, lost revenue tracking, no customer records
- **Status:** 🔄 **PENDING**
- **Plan Needed:**
  - Investigate order completion workflow
  - Check if orders are being marked as completed vs deleted
  - Implement proper order archiving logic
  - Add order status tracking (active → completed)

---

## 🔧 Technical Debt & Improvements

### **Fuzzy Search Algorithm**
- Current fuzzy matching needs improvement
- Consider implementing better similarity scoring
- May need to adjust confidence thresholds

### **Modification Handling**
- Need to implement proper modification parsing
- Should capture and store modifications in order items
- Need to display modifications in order summary

### **Restaurant Information Service**
- Question agent needs access to restaurant service
- Should be able to answer hours, location, phone, etc.
- May need to add restaurant data to question context

### **Workflow Orchestration**
- Remove item workflow needs debugging
- Modify item workflow needs debugging
- May need to add performance timing to these workflows

### **Upselling System**
- **Future Enhancement:** Implement intelligent upselling recommendations
- **Features to Add:**
  - Suggest complementary items based on current order (e.g., "Would you like fries with that burger?")
  - Recommend premium upgrades (e.g., "Upgrade to large size for just $1 more?")
  - Suggest popular add-ons (e.g., "Add a drink to complete your meal?")
  - Seasonal/promotional item suggestions
- **Implementation Approach:**
  - Create upselling agent that analyzes current order context
  - Build recommendation engine based on menu item relationships
  - Add upselling prompts to order completion workflow
  - Track upselling success rates and optimize recommendations

### **Intelligent Dietary Analysis System**
- **Future Enhancement:** AI-powered dietary restriction analysis and recommendations
- **Features to Add:**
  - Ingredient-level dietary flags (gluten-free, vegan, vegetarian, keto, sugar-free, etc.)
  - Dynamic menu item analysis based on modifications
  - AI responses to dietary questions ("What's gluten-free?", "What's vegan?")
  - Smart dietary recommendations ("Remove the bun to make it keto")
  - Allergen and dietary conflict detection
- **Implementation Approach:**
  - Add dietary fields to Ingredient model (is_gluten_free, is_vegan, is_keto, etc.)
  - Create dietary analysis service to evaluate menu items + modifications
  - Enhance question agent with dietary knowledge
  - Add dietary filtering to menu search
  - Implement dynamic dietary status calculation (e.g., "This burger becomes keto if you remove the bun")

---

## 📋 Next Steps

1. **Debug Remove Item Workflow**
   - Check if remove item workflow is being called
   - Verify order session service remove functionality
   - Test with simple remove commands

2. **Debug Modify Item Workflow**
   - Check if modify item workflow is being called
   - Verify modification parsing and storage
   - Test with simple modification commands

3. **Improve Fuzzy Search**
   - Review current fuzzy matching algorithm
   - Adjust similarity scoring
   - Test with various menu item names

4. **Add "Anything Else?" Prompt**
   - Modify add item workflow to include follow-up question
   - Ensure it only asks after successful item additions

5. **Fix Modifications**
   - Implement proper modification parsing
   - Store modifications in order items
   - Display modifications in order summary

---

## 🧪 Testing Scenarios

### **Remove Item Tests**
- [ ] "Remove the burger"
- [ ] "Take off the fries"
- [ ] "I don't want the drink"

### **Modify Item Tests**
- [ ] "Change the burger to no cheese"
- [ ] "Make the burger medium rare"
- [ ] "Add extra pickles to the burger"

### **Fuzzy Search Tests**
- [ ] "quantum burger" → should match "quantum cheeseburger"
- [ ] "cosmic fries" → should match "cosmic potato wedges"
- [ ] "space drink" → should match "space cola"

### **Modification Tests**
- [ ] "quantum cheeseburger with no cheese"
- [ ] "cosmic burger medium rare"
- [ ] "space fries extra crispy"

### **Restaurant Information Tests**
- [ ] "What are your hours?"
- [ ] "Where are you located?"
- [ ] "What's your phone number?"
- [ ] "What's your address?"

---

## 📊 Performance Notes

- **Total processing time:** ~8 seconds per voice input
- **Speech-to-text:** ~1.25 seconds
- **Intent classification:** ~0.8 seconds
- **Workflow execution:** ~0.3 seconds
- **Voice generation:** ~2.5 seconds
- **S3 upload:** ~1.5 seconds

---

## 🏷️ Labels

- `bug` - Confirmed bugs
- `enhancement` - Feature improvements
- `performance` - Performance related
- `ux` - User experience
- `core` - Core functionality
- `fuzzy-search` - Fuzzy matching issues
- `modifications` - Item modification handling
