SAMPLES = {
    "Tightly Coupled Order Processor": {
        "language": "Python",
        "code": """class OrderProcessor:
    def __init__(self, db_connection):
        self.db = db_connection

    def process(self, order):
        total = 0
        for item in order['items']:
            total += item['price'] * item['qty']
        order['total'] = total

        self.db.execute(
            "INSERT INTO orders VALUES (?, ?, ?)",
            [order['id'], order['email'], total]
        )

        import smtplib
        server = smtplib.SMTP('smtp.company.com', 587)
        server.login('orders@company.com', 'pass123')
        server.sendmail(
            'orders@company.com',
            order['email'],
            f"Order {order['id']} confirmed! Total: ${total}"
        )
        server.quit()

        for item in order['items']:
            self.db.execute(
                "UPDATE inventory SET qty = qty - ? WHERE sku = ?",
                [item['qty'], item['sku']]
            )
""",
        "context": "This is a legacy e-commerce backend we inherited. All business logic lives in this one class.",
    },
    "Unsafe File Parser": {
        "language": "Python",
        "code": """import os

def parse_config(path):
    config = {}
    f = open(path, 'r')
    for line in f:
        if '=' in line:
            k, v = line.split('=', 1)
            config[k.strip()] = v.strip()
    return config

def load_all_configs(directory):
    result = {}
    for filename in os.listdir(directory):
        if filename.endswith('.cfg'):
            name = filename[:-4]
            result[name] = parse_config(directory + '/' + filename)
    return result

settings = load_all_configs('./configs')
db_password = settings['database']['password']
os.system(f'mysqldump -u admin -p{db_password} --all-databases > backup.sql')
""",
        "context": "A configuration loader used in our deployment pipeline. It reads .cfg files and shells out to mysqldump.",
    },
    "React Component with State Issues": {
        "language": "TypeScript",
        "code": """import React, { useState, useEffect } from 'react';

function UserDashboard() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    fetch('/api/users')
      .then(res => res.json())
      .then(data => setUsers(data));
    setLoading(false);
  }, []);

  const filtered = users.filter(u => 
    u.name.includes(search) || u.email.includes(search)
  );

  return (
    <div>
      <input value={search} onChange={e => setSearch(e.target.value)} />
      {loading && <p>Loading...</p>}
      {filtered.map(user => (
        <div key={user.id}>
          <h3>{user.name}</h3>
          <p>{user.email}</p>
        </div>
      ))}
    </div>
  );
}

export default UserDashboard;
""",
        "context": "Early-stage startup dashboard. We're iterating fast and want to catch issues before they hit production.",
    },
    "Poorly-Named Utility Functions": {
        "language": "JavaScript",
        "code": """function f1(a) {
    var x = [];
    for (var i = 0; i < a.length; i++) {
        if (a[i].active) {
            x.push(a[i]);
        }
    }
    return x;
}

function f2(b) {
    var y = 0;
    for (var j = 0; j < b.length; j++) {
        y = y + b[j].amount;
    }
    return y;
}

function f3(c, d) {
    for (var k = 0; k < c.length; k++) {
        if (c[k].id === d) {
            return c[k];
        }
    }
    return null;
}

function doStuff(data, userId) {
    var active = f1(data);
    var total = f2(active);
    var user = f3(data, userId);
    return {
        active: active,
        total: total,
        user: user
    };
}
""",
        "context": "Code recovered from a former contractor. No documentation exists.",
    },
}
