# Government Link Comparator

## 🎯 What This Does

This is a **separate system** that does exactly what you requested:

1. **Collects links** like the initial "add new task" does
2. **Compares old XML with new XML** to find new/updated links
3. **Puts new links in latest updates page** automatically
4. **Deletes old XML, keeps new one** for next comparison

## 🚫 What It Does NOT Do

- ❌ **Does NOT touch the sitemap dashboard** (that's completely separate)
- ❌ **Does NOT use sitemap fetcher** (uses the same collection method as add task)
- ❌ **Does NOT interfere with existing sitemap system**

## 📁 Files Created

- `government_link_comparator.py` - Main comparator class
- `test_government_comparator.py` - Test script to try it out
- `GOVERNMENT_COMPARATOR_README.md` - This file

## 🔧 How It Works

### 1. **Collection Phase**
- Uses the **exact same** `collect_links_to_xml()` function from your app
- Creates new XML file with current timestamp
- Saves to `collections/` directory

### 2. **Comparison Phase**
- Finds the **previous XML file** for the same domain
- Extracts URLs from both old and new XML
- Identifies **new URLs only** (new - old)

### 3. **Update Phase**
- Stores new URLs in `sitemap_updates` table
- Shows up immediately on Latest Updates page
- Updates government dashboard comparison status

### 4. **Cleanup Phase**
- **Deletes old XML file** (and .txt, .json if they exist)
- **Keeps new XML file** for next comparison
- Maintains clean file structure

## 🚀 How to Use

### Option 1: Use the "Run All" Button
1. Go to Government Dashboard
2. Click "Run All" button
3. System automatically:
   - Collects new links from all sites
   - Compares with previous data
   - Finds new URLs
   - Updates latest updates page
   - Cleans up old files

### Option 2: Test Manually
```bash
python3 test_government_comparator.py
```

### Option 3: Use in Code
```python
from government_link_comparator import GovernmentLinkComparator

comparator = GovernmentLinkComparator()

# Process single site
result = comparator.process_site("https://example.com")

# Process all sites
results = comparator.process_all_sites()
```

## 📊 What Happens When You Click "Run All"

1. **🔄 Collection**: Fetches fresh links from all government sites
2. **🔍 Comparison**: Compares new XML with previous XML
3. **📝 Database**: Stores new URLs in `sitemap_updates` table
4. **🗑️ Cleanup**: Deletes old XML, keeps new one
5. **📋 Updates**: New URLs appear on Latest Updates page
6. **✅ Status**: Dashboard shows comparison results

## 🎯 Key Benefits

- **Simple**: Uses existing collection method, no complex sitemap logic
- **Clean**: Automatically manages file cleanup
- **Fast**: Only processes what's needed
- **Separate**: Doesn't interfere with sitemap dashboard
- **Integrated**: Works seamlessly with existing system

## 🔍 File Management

- **New XML**: `collections/domain_timestamp.xml` (kept for next comparison)
- **Old XML**: Automatically deleted after comparison
- **Database**: New URLs stored in `sitemap_updates` table
- **Cleanup**: Automatic removal of old files

## 🧪 Testing

Run the test script to see it in action:
```bash
python3 test_government_comparator.py
```

This will let you test with a single site or all sites to see exactly how it works.

## 📝 Summary

This system does **exactly** what you asked for:
- ✅ Collects links like add task
- ✅ Compares old vs new XML
- ✅ Finds new links
- ✅ Updates latest updates page
- ✅ Deletes old XML, keeps new one
- ✅ **Separate from sitemap dashboard**
- ✅ **Uses existing collection method**

No sitemap complexity, no interference with existing systems, just simple link collection and comparison! 🎯
