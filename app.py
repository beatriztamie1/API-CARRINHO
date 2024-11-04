from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user , current_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'minha_chave_123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'

login_Manager = LoginManager()
login_Manager.init_app(app)
login_Manager.login_view = 'login'  # Configuração do login_view
db = SQLAlchemy(app)
CORS(app)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    password = db.Column(db.String(120), nullable=False)
    cart = db.relationship('CartItem', backref='user', lazy=True)  # Corrigido 'cartItem' para 'CartItem'



# Autenticação
@login_Manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/login', methods=["POST"])
def login(): 
    data = request.json 
    user = User.query.filter_by(username=data.get("username")).first()

    if user and data.get("password") == user.password:
        login_user(user)
        return jsonify({"message": "Logged in successfully"})
    
    return jsonify({"message": "Unauthorized. Invalid credentials"}), 401

# Modelagem
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True)


class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)

@app.route('/api/products/add', methods=["POST"])
@login_required
def add_product():
    data = request.json
    print(data)  # Adicione isso para verificar o que está sendo recebido
    if "name" in data and "price" in data and isinstance(data["price"], (int, float)) and data["price"] > 0:
        product = Product(
            name=data["name"],
            price=data["price"],
            description=data.get("description", "")
        )
        db.session.add(product)
        db.session.commit()
        return jsonify({"message": "Produto adicionado com sucesso!"}), 201

    return jsonify({"message": "Dados do produto inválidos!"}), 400

    
@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logout sucessfully"})
@app.route('/api/products/delete/<int:product_id>', methods=["DELETE"])
@login_required
def delete_product(product_id):
    product = Product.query.get(product_id)
    if product:
        db.session.delete(product)
        db.session.commit()
        return jsonify({"message": "Produto deletado com sucesso!"})

    return jsonify({"message": "Produto não encontrado!"}), 404



@app.route('/api/products/<int:product_id>', methods=["GET"])
def get_product_details(product_id):
    product = Product.query.get(product_id)
    if product:
        return jsonify({
            "id": product.id,
            "name": product.name,
            "price": product.price,
            "description": product.description
        })
    return jsonify({"message": "Produto não encontrado!"}), 404

@app.route('/api/products/update/<int:product_id>', methods=["PUT"])
@login_required
def update_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"message": "Produto não encontrado!"}), 404
    
    data = request.json
    if "name" in data:
        product.name = data['name']

    if "price" in data and isinstance(data["price"], (int, float)) and data["price"] > 0:
        product.price = data['price']

    if "description" in data:
        product.description = data['description']  

    db.session.commit()
    return jsonify({"message": "Produto atualizado com sucesso!"})

@app.route('/api/products', methods=["GET"])
def get_products():
    products = Product.query.all()
    product_list = []
    
    for product in products:
        product_data = {
            "id": product.id,
            "name": product.name,
            "price": product.price,
            "description": product.description
        }
        product_list.append(product_data)
    
    return jsonify(product_list)

#checkout carrinho produto login

@app.route('/api/cart/add/<int:product_id>', methods=["POST"])
@login_required
def add_to_cart(product_id):
    # Usuário
    user = User.query.get(int(current_user.id))
    product = Product.query.get(product_id)

    if user and product:
        cart_item = CartItem(user_id=user.id, product_id=product.id)
        db.session.add(cart_item)
        db.session.commit()
        return jsonify({"message": "Item added to the cart successfully"})
    return jsonify({"message": "Failed to add to the cart"}), 400


@app.route('/api/cart/remove/<int:product_id>', methods=["DELETE"])
@login_required
def remove_from_cart(product_id):
    cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if cart_item:
        db.session.delete(cart_item)
        db.session.commit()
        return jsonify({"message": "Item removed from the cart successfully"}), 200
    return jsonify({"message": "Failed to remove item from the cart"}), 400

    
@app.route('/api/cart', methods=["GET"])
@login_required
def view_cart():
    user = User.query.get(current_user.id)
    cart_items = user.cart 
    cart_content = []

    for cart_item in cart_items:
        product = Product.query.get(cart_item.product_id)  # Mover a busca do produto para dentro do loop
        if product:  # Verifica se o produto existe
            cart_content.append({
                "id": cart_item.id,
                "user_id": cart_item.user_id,
                "product_id": cart_item.product_id,
                "product_name": product.name,
                "product_price": product.price
            })
    
    return jsonify(cart_content), 200  # Adicionar status 200 à resposta


@app.route('/api/cart/checkout', methods=["POST"])
@login_required
def checkout():
    user = User.query.get(int(current_user.id))
    cart_items = user.cart 
    for cart_item in cart_items:
        db.session.delete(cart_item)
    db.session.commit()
    return jsonify({"message": "Checkout sucessful. Cart has been cleared."}), 


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
