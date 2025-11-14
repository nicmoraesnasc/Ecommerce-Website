import mysql.connector
import os
import logging
from werkzeug.security import generate_password_hash, check_password_hash

logger = logging.getLogger('werkzeug')

class Database:
  def __init__(self, host, db_name, db_user, db_password):

    self.mydb = mysql.connector.connect(
      host=host,
      user=db_user,
      password=db_password,
      database=db_name
    )

    self.mycursor = self.mydb.cursor()

    self.mycursor.execute("""
        CREATE TABLE IF NOT EXISTS User (
            id INT AUTO_INCREMENT PRIMARY KEY, 
            name VARCHAR(255), 
            last_name VARCHAR(255), 
            phone VARCHAR(11),
            zip_code VARCHAR(11) NULL,
            state VARCHAR(255), 
            city VARCHAR(255),
            neighborhood VARCHAR(255),
            address VARCHAR(255),
            house_number INT,
            email VARCHAR(255) UNIQUE, 
            password VARCHAR(255), 
            is_admin TINYINT
        );
        """)
    
    self.mycursor.execute("""
        CREATE TABLE IF NOT EXISTS SocialMedia (
            id INT AUTO_INCREMENT PRIMARY KEY,
            social_name VARCHAR(255),
            social_link VARCHAR(255)
        );
    """)
    
    self.mycursor.execute("""
        CREATE TABLE IF NOT EXISTS About (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(255),
            content TEXT
        );
        """)

    self.mycursor.execute("""
        CREATE TABLE IF NOT EXISTS Product (
            id INT AUTO_INCREMENT PRIMARY KEY, 
            product_name VARCHAR(255), 
            product_desc VARCHAR(255), 
            product_price FLOAT, 
            image_path VARCHAR(255)
        );
        """)
    
    self.mycursor.execute("""
        CREATE TABLE IF NOT EXISTS Cart (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            FOREIGN KEY (user_id) REFERENCES User(id) ON DELETE CASCADE
        );
        """)
    
    self.mycursor.execute("""
        CREATE TABLE IF NOT EXISTS CartItem (
            id INT AUTO_INCREMENT PRIMARY KEY,
            cart_id INT,
            product_id INT,
            quantity INT, 
            price FLOAT,
            FOREIGN KEY (cart_id) REFERENCES Cart(id),
            FOREIGN KEY (product_id) REFERENCES Product(id)
        );
        """)

    self.mycursor.execute("""
        CREATE TABLE IF NOT EXISTS `Order` (
            id INT AUTO_INCREMENT PRIMARY KEY,
            tracking_code VARCHAR(50) NULL,
            user_id INT NOT NULL,
            order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_price DECIMAL(10,2) NOT NULL,
            confirmed_payment TINYINT(1) DEFAULT 1,  # 1 = true (pago)
            shipped TINYINT(1) DEFAULT 0,
            completed TINYINT(1) DEFAULT 0,
            shipping_address VARCHAR(255),
            shipping_house_number INT,
            shipping_city VARCHAR(255),
            shipping_state VARCHAR(255),
            shipping_zip_code VARCHAR(11),
            payment_status ENUM('pendente', 'pago', 'erro', 'estornado') DEFAULT 'pago',
            shipping_status ENUM('pendente', 'enviado') DEFAULT 'pendente',
            FOREIGN KEY (user_id) REFERENCES User(id) ON DELETE CASCADE
        );
    """)
      
    self.mycursor.execute("""
        CREATE TABLE IF NOT EXISTS OrderItem (
            id INT AUTO_INCREMENT PRIMARY KEY,
            order_id INT,
            product_id INT,
            quantity INT, 
            price FLOAT,
            FOREIGN KEY (order_id) REFERENCES `Order`(id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES Product(id)
        );
        """)

    self.mydb.commit()

  def insert_user(self, name, last_name, phone, zip_code, state, city, neighborhood, address, house_number, email, password, is_admin):
    hashed_password = generate_password_hash(password)
    query = """
        INSERT INTO User 
        (name, last_name, phone, zip_code, state, city, neighborhood, address, house_number, email, password, is_admin)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    values = (name, last_name, phone, zip_code, state, city, neighborhood, address, house_number, email, hashed_password, is_admin)
    self.mycursor.execute(query, values)
    self.mydb.commit()


  def select_user(self, email, password):
    self.mycursor.execute(f" SELECT * FROM User WHERE email = '{email}';")
    user = []
    result = self.mycursor.fetchall()

    for row in result:
      user.append(row)

    print(user)
    print(user[0])
    print(user[0][7])

    check_password_hash(user[0][7], password)
    return user
  
  def verify_password(self, email, password):
    self.mycursor.execute(f" SELECT id, password FROM User WHERE email = '{email}';")
    hashed_password = []
    result = self.mycursor.fetchall()

    for row in result:
      hashed_password.append(row)

    print(hashed_password[0][0])

    return hashed_password[0][0], check_password_hash(hashed_password[0][1], password)

     
  
  def select_user_by_id(self, user_id):
    query = """
    SELECT 
        id, 
        name,           -- user[1]
        last_name,      -- user[2] 
        phone,          -- user[3]
        state,          -- user[4] 
        city,           -- user[5]
        email,          -- user[6]
        password,       -- user[7]
        is_admin,       -- user[8]
        zip_code,       -- user[9]
        neighborhood,   -- user[10]
        address,        -- user[11]
        house_number    -- user[12]
    FROM User 
    WHERE id = %s
    """
    self.mycursor.execute(query, (user_id,))
    result = self.mycursor.fetchall()
    
    user = []
    for row in result:
        user.append(row)
    return user
  
  def update_user(self, id, name=None, last_name=None, phone=None, zip_code=None,
                state=None, city=None, neighborhood=None, address=None, house_number=None,
                email=None, password=None):
    updates = []
    values = []

    if name:
        updates.append("name = %s")
        values.append(name)
    if last_name:
        updates.append("last_name = %s")
        values.append(last_name)
    if phone:
        updates.append("phone = %s")
        values.append(phone)
    if zip_code:
        updates.append("zip_code = %s")
        values.append(zip_code)
    if state:
        updates.append("state = %s")
        values.append(state)
    if city:
        updates.append("city = %s")
        values.append(city)
    if neighborhood:
        updates.append("neighborhood = %s")
        values.append(neighborhood)
    if address:
        updates.append("address = %s")
        values.append(address)
    if house_number:
        updates.append("house_number = %s")
        values.append(house_number)
    if email:
        updates.append("email = %s")
        values.append(email)
    if password:
        updates.append("password = %s")
        values.append(password)

    if updates:
        query = f"UPDATE User SET {', '.join(updates)} WHERE id = %s"
        values.append(id)
        self.mycursor.execute(query, tuple(values))
        self.mydb.commit()

  def update_user_without_password(self, id, name=None, last_name=None, phone=None, zip_code=None,
                                state=None, city=None, neighborhood=None, address=None, 
                                house_number=None, email=None):
    updates = []
    values = []

    if name:
        updates.append("name = %s")
        values.append(name)
    if last_name:
        updates.append("last_name = %s")
        values.append(last_name)
    if phone:
        updates.append("phone = %s")
        values.append(phone)
    if zip_code:
        updates.append("zip_code = %s")
        values.append(zip_code)
    if state:
        updates.append("state = %s")
        values.append(state)
    if city:
        updates.append("city = %s")
        values.append(city)
    if neighborhood:
        updates.append("neighborhood = %s")
        values.append(neighborhood)
    if address:
        updates.append("address = %s")
        values.append(address)
    if house_number:
        updates.append("house_number = %s")
        values.append(house_number)
    if email:
        updates.append("email = %s")
        values.append(email)

    if updates:
        query = f"UPDATE User SET {', '.join(updates)} WHERE id = %s"
        values.append(id)
        self.mycursor.execute(query, tuple(values))
        self.mydb.commit()

  def get_users(self):
    self.mycursor.execute("SELECT * FROM User;")
    users = []
    results = self.mycursor.fetchall()
    for row in results:
      users.append(row)
    return users
  
  def is_admin(self, user_id):
    try:
        if not user_id or int(user_id) == 0:
            return False
        user = self.select_user_by_id(user_id)
        if not user or len(user[0]) <= 8:
            return False
        return bool(user[0][8])
    except Exception as e:
        print(f"Erro ao verificar admin: {e}")
        return False
    

  def delete_user(self, user_id):
        try:
            self.clear_cart(user_id) 
            cart_id = self.get_cart_id(user_id)
            if cart_id:
                self.mycursor.execute("DELETE FROM Cart WHERE id = %s", (cart_id,))
            
            self.mycursor.execute("DELETE FROM OrderItem WHERE order_id IN (SELECT id FROM `Order` WHERE user_id = %s)", (user_id,))
            self.mycursor.execute("DELETE FROM `Order` WHERE user_id = %s", (user_id,))
            
            self.mycursor.execute("DELETE FROM User WHERE id = %s", (user_id,))
            self.mydb.commit()
        except Exception as e:
            self.mydb.rollback()
            logger.error(f"Erro ao deletar usuário: {e}")


  def insert_product(self, product_name, product_desc, product_price, image_path=None):
      if image_path:
          query = "INSERT INTO Product (product_name, product_desc, product_price, image_path) VALUES (%s, %s, %s, %s)"
          values = (product_name, product_desc, product_price, image_path)
      else:
          query = "INSERT INTO Product (product_name, product_desc, product_price) VALUES (%s, %s, %s)"
          values = (product_name, product_desc, product_price)
      
      self.mycursor.execute(query, values)
      self.mydb.commit()
    
  def get_products(self):
    self.mycursor.execute("SELECT * FROM Product;")
    products = []
    results = self.mycursor.fetchall()
    for row in results:
      products.append(row)
    return products
  
  def get_product_by_id(self, product_id):
    self.mycursor.execute(f"SELECT * FROM Product WHERE id = '{product_id}';")
    product = []
    result = self.mycursor.fetchall()

    if not result:
      return None
  
    for row in result:
      product.append(row)
    return product[0]

  def update_product(self, product_id, product_name, product_desc, product_price, image_path=None):
      if image_path:
          query = "UPDATE Product SET product_name = %s, product_desc = %s, product_price = %s, image_path = %s WHERE id = %s"
          values = (product_name, product_desc, product_price, image_path, product_id)
      else:
          query = "UPDATE Product SET product_name = %s, product_desc = %s, product_price = %s WHERE id = %s"
          values = (product_name, product_desc, product_price, product_id)
      
      self.mycursor.execute(query, values)
      self.mydb.commit()

  def delete_product(self, product_id):
    try:
        self.mycursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        self.mycursor.execute("DELETE FROM CartItem WHERE product_id = %s", (product_id,))
        self.mycursor.execute("DELETE FROM OrderItem WHERE product_id = %s", (product_id,))
        
        product = self.get_product_by_id(product_id)
        if product and product[4]:
            img_path = os.path.join('static', 'uploads', product[4])
            if os.path.exists(img_path):
                os.remove(img_path)
        
        self.mycursor.execute("DELETE FROM Product WHERE id = %s", (product_id,))
        self.mydb.commit()
        return True
    except Exception as e:
        self.mydb.rollback()
        logger.error(f"Error deleting product: {str(e)}")
        return False
    finally:
        self.mycursor.execute("SET FOREIGN_KEY_CHECKS = 1")

  def select_product(self, product_id):
    self.mycursor.execute(f"SELECT * FROM Product WHERE id = {product_id};")
    product = []
    result = self.mycursor.fetchall()
    for row in result:
      product.append(row)
    return product

  def insert_cart(self, user_id):
    self.mycursor.execute("SELECT * FROM Cart WHERE user_id = %s", (user_id,))
    cart = self.mycursor.fetchone()
    if not cart:
      self.mycursor.execute(f"INSERT INTO Cart (user_id) VALUES ('{str(user_id)}')")
      self.mydb.commit()

  def insert_cart_item(self, cart_id, product_id, quantity, price):
    self.mycursor.execute(f"INSERT INTO CartItem (cart_id, product_id, quantity, price) VALUES ('{str(cart_id)}', '{str(product_id)}', '{str(quantity)}', '{str(price)}')")
    self.mydb.commit()

  def get_cart_items(self, user_id):
    self.mycursor.execute("SELECT * FROM CartItem WHERE id = %s", (user_id,))
    cart_items = []
    results = self.mycursor.fetchall()
    for row in results:
      cart_items.append(row)
    return cart_items

  def insert_order(self, tracking_code, user_id, order_date, total_price, 
                confirmed_payment=1, shipped=0, completed=0, 
                shipping_address=None, shipping_house_number=None, shipping_city=None, 
                shipping_state=None, shipping_zip_code=None,
                payment_status='pago', shipping_status='pendente'):
    
    # DEBUG: Verificar o que está chegando
    print(f"INSERT_ORDER DEBUG - Tracking code recebido: '{tracking_code}'")
    print(f"INSERT_ORDER DEBUG - Tipo: {type(tracking_code)}")
    
    try:
        valid_payment = ['pendente', 'pago', 'erro', 'estornado']
        valid_shipping = ['pendente', 'enviado']
        
        payment_status = payment_status if payment_status in valid_payment else 'pago'
        shipping_status = shipping_status if shipping_status in valid_shipping else 'pendente'
        
        query = """
            INSERT INTO `Order` 
            (tracking_code, user_id, order_date, total_price,
            confirmed_payment, shipped, completed,
            shipping_address, shipping_house_number, shipping_city, shipping_state,
            shipping_zip_code, payment_status, shipping_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            tracking_code,
            user_id,
            order_date,
            total_price,
            confirmed_payment,
            shipped,
            completed,
            shipping_address,
            shipping_house_number,
            shipping_city,
            shipping_state,
            shipping_zip_code,
            payment_status,
            shipping_status
        )
        
        print(f"INSERT_ORDER DEBUG - Valores que serão inseridos: {values}")
        
        self.mycursor.execute(query, values)
        self.mydb.commit()
        
        # Verificar o que foi realmente inserido
        order_id = self.mycursor.lastrowid
        self.mycursor.execute("SELECT tracking_code FROM `Order` WHERE id = %s", (order_id,))
        result = self.mycursor.fetchone()
        print(f"INSERT_ORDER DEBUG - Tracking code após inserção: '{result[0] if result else None}'")
        
        return True
    except mysql.connector.Error as err:
        logger.error(f"Erro ao inserir pedido: {err}")
        return False
    
  def insert_order_item(self, order_id, product_id, quantity, price):
    self.mycursor.execute("SELECT id FROM Product WHERE id = %s", (product_id,))
    product = self.mycursor.fetchone()
    if not product:
        raise ValueError(f"Produto com ID {product_id} não encontrado!")
    self.mycursor.execute("""
        INSERT INTO OrderItem (order_id, product_id, quantity, price)
        VALUES (%s, %s, %s, %s)
    """, (order_id, product_id, quantity, price))
    self.mydb.commit()

  def get_order_by_tracking(self, tracking_code):
      self.mycursor.execute("""
          SELECT tracking_code, order_date, total_price, 
            shipping_address, shipping_house_number, shipping_city, shipping_state, shipping_zip_code
          FROM `Order`
          WHERE tracking_code = %s
      """, (tracking_code,))
      result = self.mycursor.fetchone()
      if result:
          columns = [col[0] for col in self.mycursor.description]
          return dict(zip(columns, result))
      return None

  def get_cart_id(self, user_id):
      self.mycursor.execute("SELECT id FROM Cart WHERE user_id = %s", (user_id,))
      cart = self.mycursor.fetchone()
      if cart:
          return cart[0]
      return None

  def get_full_cart_items(self, user_id):
      cart_id = self.get_cart_id(user_id)
      if not cart_id:
          return []
      
      self.mycursor.execute("""
          SELECT 
              CartItem.id, 
              Product.id as product_id,  # Certifique-se de incluir isso
              Product.product_name, 
              CartItem.quantity, 
              CartItem.price,
              (CartItem.quantity * CartItem.price) as total_price
          FROM CartItem
          JOIN Product ON CartItem.product_id = Product.id
          WHERE CartItem.cart_id = %s
      """, (cart_id,))
      
      columns = [col[0] for col in self.mycursor.description]
      return [dict(zip(columns, row)) for row in self.mycursor.fetchall()]

  def update_cart_item(self, item_id, quantity):
      self.mycursor.execute("""
          UPDATE CartItem 
          SET quantity = %s 
          WHERE id = %s
      """, (quantity, item_id))
      self.mydb.commit()

  def remove_cart_item(self, item_id):
      self.mycursor.execute("DELETE FROM CartItem WHERE id = %s", (item_id,))
      self.mydb.commit()

  def clear_cart(self, user_id):
      cart_id = self.get_cart_id(user_id)
      if cart_id:
          self.mycursor.execute("DELETE FROM CartItem WHERE cart_id = %s", (cart_id,))
          self.mydb.commit()

  def get_user_orders(self, user_id):
    self.mycursor.execute("""
        SELECT id, tracking_code, order_date, total_price, 
            payment_status, shipping_status
        FROM `Order`
        WHERE user_id = %s
        ORDER BY order_date DESC
    """, (user_id,))
    
    columns = [col[0] for col in self.mycursor.description]
    return [dict(zip(columns, row)) for row in self.mycursor.fetchall()]

  def get_order_items(self, order_id):
      self.mycursor.execute("""
          SELECT oi.quantity, oi.price, 
                p.product_name, p.product_desc
          FROM OrderItem oi
          JOIN Product p ON oi.product_id = p.id
          WHERE oi.order_id = %s
      """, (order_id,))
      
      columns = [col[0] for col in self.mycursor.description]
      return [dict(zip(columns, row)) for row in self.mycursor.fetchall()]
  
  def insert_order_and_get_id(self, tracking_code, user_id, total_price, **shipping_info):
    try:
        query = """
            INSERT INTO `Order` 
            (tracking_code, user_id, total_price,
             shipping_address, shipping_house_number, shipping_city, shipping_state, shipping_zip_code)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            tracking_code,  # Pode ser None
            user_id,
            total_price,
            shipping_info.get('shipping_address'),
            shipping_info.get('shipping_house_number'),
            shipping_info.get('shipping_city'),
            shipping_info.get('shipping_state'),
            shipping_info.get('shipping_zip_code')
        )
        
        self.mycursor.execute(query, values)
        self.mydb.commit()
        return self.mycursor.lastrowid
        
    except mysql.connector.Error as err:
        logger.error(f"Erro ao criar pedido: {err}")
        return None
    
  def get_all_orders(self, status_filter='all', search_query=''):
        query = """
            SELECT o.id, o.tracking_code, u.email as user_email, 
                o.order_date, o.total_price, o.shipping_status,
                o.payment_status, o.shipping_address, o.shipping_house_number, 
                o.shipping_city, o.shipping_state, o.shipping_zip_code
            FROM `Order` o
           
            JOIN User u ON o.user_id = u.id
        """
        
        conditions = []
        params = []
        
        if status_filter != 'all':
            conditions.append("o.shipping_status = %s")
            params.append(status_filter)
        
        if search_query:
            conditions.append("(o.tracking_code LIKE %s OR u.email LIKE %s)")
            params.extend([f"%{search_query}%", f"%{search_query}%"])
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY o.order_date DESC"
        
        cursor = self.mydb.cursor(dictionary=True)
        cursor.execute(query, tuple(params))
        return cursor.fetchall()


  def get_order_details(self, order_id):
    query_order = """
        SELECT
            o.id,
            o.tracking_code,
            u.email AS user_email,
            u.name AS user_name,
            u.phone AS user_phone,
            o.order_date,
            o.total_price,
            o.shipping_status,
            o.payment_status,
            o.shipping_address,
            o.shipping_house_number,
            o.shipping_city,
            o.shipping_state,
            o.shipping_zip_code
        FROM `Order` o
        JOIN User u ON o.user_id = u.id
        WHERE o.id = %s
    """
    cursor = self.mydb.cursor(dictionary=True)
    cursor.execute(query_order, (order_id,))
    order = cursor.fetchone()

    if not order:
        return None, None  # importante retornar dupla

    query_items = """
        SELECT
            oi.quantity,
            oi.price,
            p.product_name AS product_name
        FROM OrderItem oi
        JOIN Product p ON oi.product_id = p.id
        WHERE oi.order_id = %s
    """
    cursor.execute(query_items, (order_id,))
    order_items = cursor.fetchall()

    return order, order_items



  def update_order_status(self, order_id, shipping_status, payment_status, tracking_code):
    # DEBUG no database
    print(f"DATABASE DEBUG - Valores recebidos:")
    print(f"  shipping_status: '{shipping_status}' (tipo: {type(shipping_status)})")
    print(f"  payment_status: '{payment_status}' (tipo: {type(payment_status)})")
    print(f"  tracking_code: '{tracking_code}'")
    
    query = """
    UPDATE `Order` 
    SET shipping_status = %s, payment_status = %s, tracking_code = %s
    WHERE id = %s
    """
    
    try:
        self.mycursor.execute(query, (shipping_status, payment_status, tracking_code, order_id))
        self.mydb.commit()
        print("UPDATE executado com sucesso!")
    except Exception as e:
        print(f"ERRO no execute: {e}")
        raise

  def select_user_by_email(self, email):
        self.mycursor.execute("SELECT * FROM User WHERE email = %s", (email,))
        return self.mycursor.fetchall()

  def get_about(self):
    print("=== DEBUG GET_ABOUT ===")
    try:
        self.mycursor.execute("SELECT * FROM About")
        row = self.mycursor.fetchone()
        print(f"Row from DB: {row}")
        
        if row:
            result = {'id': row[0], 'title': row[1], 'content': row[2]}
            print(f"Returning: {result}")
            return result
        else:
            print("No row found in About table")
            return None
    except Exception as e:
        print(f"Error in get_about: {e}")
        return None

  def set_about(self, title, content):
    print(f"=== DEBUG SET_ABOUT ===")
    print(f"Received - Title: '{title}', Content: '{content}'")
    
    try:
        # Verifica se existe algum registro
        self.mycursor.execute("SELECT COUNT(*) FROM About")
        count = self.mycursor.fetchone()[0]
        print(f"Current rows in About: {count}")
        
        if count == 0:
            print("Doing INSERT...")
            self.mycursor.execute(
                "INSERT INTO About (id, title, content) VALUES (1, %s, %s)",
                (title, content)
            )
        else:
            print("Doing UPDATE...")
            self.mycursor.execute(
                "UPDATE About SET title = %s, content = %s WHERE id = 1",
                (title, content)
            )
        
        self.mydb.commit()
        print("Commit successful!")
        
        # Verifica se realmente salvou
        self.mycursor.execute("SELECT * FROM About")
        saved_row = self.mycursor.fetchone()
        print(f"After save - Row: {saved_row}")
        
    except Exception as e:
        print(f"Error in set_about: {e}")
        self.mydb.rollback()

  def get_social_media(self):
    try:
        self.mycursor.execute("SELECT * FROM SocialMedia ORDER BY id")
        return self.mycursor.fetchall()
    except Exception as e:
        print(f"Erro ao buscar redes sociais: {e}")
        return []