const fs = require('fs');
const path = require('path');

const map = {
  'XIcon': 'X',
  'ChevronUpIcon': 'ChevronUp',
  'ChevronDownIcon': 'ChevronDown',
  'ChevronLeftIcon': 'ChevronLeft',
  'ChevronRightIcon': 'ChevronRight',
  'CheckIcon': 'Check',
  'GripVerticalIcon': 'GripVertical',
  'MoreHorizontalIcon': 'MoreHorizontal',
  'MinusIcon': 'Minus',
  'CircleIcon': 'Circle',
  'SearchIcon': 'Search',
  'PanelLeftIcon': 'PanelLeft',
  'CheckCircle2': 'CircleCheck',
  'CheckCircle': 'CircleCheckBig',
  'AlertCircle': 'CircleAlert',
  'AlertTriangle': 'TriangleAlert',
  'Edit2': 'Pencil'
};

function walk(dir) {
  let results = [];
  const list = fs.readdirSync(dir);
  list.forEach(file => {
    file = path.join(dir, file);
    const stat = fs.statSync(file);
    if (stat && stat.isDirectory()) { 
      results = results.concat(walk(file));
    } else { 
      if (file.endsWith('.ts') || file.endsWith('.tsx')) {
        results.push(file);
      }
    }
  });
  return results;
}

const files = walk('./src');

files.forEach(file => {
  let content = fs.readFileSync(file, 'utf8');
  let changed = false;

  // We need to replace occurrences of these icons.
  // It's safe to just replace the word if it's imported from lucide-react.
  // Actually, standard global replace is fine as long as we only match word boundaries.
  for (const [oldName, newName] of Object.entries(map)) {
    const regex = new RegExp(`\\b${oldName}\\b`, 'g');
    if (regex.test(content)) {
      content = content.replace(regex, newName);
      changed = true;
    }
  }

  if (changed) {
    fs.writeFileSync(file, content, 'utf8');
    console.log(`Updated ${file}`);
  }
});

console.log("Done");
