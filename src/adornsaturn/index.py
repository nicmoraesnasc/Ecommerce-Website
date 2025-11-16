from flask import (
    Flask,
    redirect,
    url_for,
    request,
    render_template,
    Blueprint,
    flash,
    session,
    abort,
    jsonify,
)
from database import Database
from flask import Flask, jsonify
import requests
import logging
import sys
import json
from datetime import datetime
import random
import string
from flask import flash
import os
from werkzeug.utils import secure_filename
from flask import send_from_directory

logger = logging.getLogger("werkzeug")

app = Flask(__name__)
app.secret_key = "1234"
site = Blueprint("site", __name__, template_folder="templates")

db_host = os.environ.get("ADORNSATURN_DB_HOST", "localhost")
db_name = os.environ.get("ADORNSATURN_DB_NAME", "adornsaturn")
db_user = os.environ.get("ADORNSATURN_DB_USER", "root")
db_password = os.environ.get("ADORNSATURN_DB_PASSWORD", "root")

database = Database(db_host, db_name, db_user, db_password)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "adornsaturn", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}


os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # Limite de 5MB


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/estados")
def estados():
    url = "https://servicodados.ibge.gov.br/api/v1/localidades/estados"
    r = requests.get(url)
    estados = sorted(r.json(), key=lambda x: x["nome"])
    return jsonify(estados)


@app.route("/cidades/<uf>")
def cidades(uf):
    url = f"https://servicodados.ibge.gov.br/api/v1/localidades/estados/{uf}/municipios"
    r = requests.get(url)
    cidades = sorted(r.json(), key=lambda x: x["nome"])
    return jsonify(cidades)


@app.route("/", methods=["GET", "POST"])
def index():
    user_id = 0
    if "user_id" in session:

        if int(session["user_id"]) == 0:

            return redirect(url_for("login"))

        user_id = session["user_id"]
    else:
        return redirect(url_for("login"))

    return redirect(url_for("products"))


@app.route("/login", methods=["GET", "POST"])
def login():

    login_failed = False

    if (
        request.method == "POST"
        and "email" in request.form
        and "password" in request.form
    ):

        email = request.form["email"]
        password = request.form["password"]

        user_id, login_valid = database.verify_password(email, password)

        if not login_valid:
            login_failed = True
            session["user_id"] = 0
        else:
            session["user_id"] = int(user_id)

            # TODO: verificar se usuario possui carrinho
            #       se nao possuir carrinho, criar um.
            return redirect(url_for("index"))

    return render_template("auth/login.html", login_failed=login_failed)


@app.route("/logout", methods=["GET", "POST"])
def logout():
    session["user_id"] = 0
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    return render_template("auth/register.html")


@app.route("/user/create", methods=["GET", "POST"])
def create_user():
    if request.method == "POST":
        name = request.form["name"]
        last_name = request.form["last_name"]
        phone = request.form["phone"]
        zip_code = request.form["zip_code"]
        state = request.form["state"]
        city = request.form["city"]
        neighborhood = request.form["neighborhood"]
        address = request.form["address"]
        house_number = request.form["house_number"]
        email = request.form["email"]
        password = request.form["password"]
        password_c = request.form["password_c"]

        # Valida senha
        password_incorrect = password != password_c

        # Verifica se e-mail já existe
        existing_user = database.select_user_by_email(email)
        if existing_user:
            error = "Este e-mail já está cadastrado."
            return render_template("auth/register.html", error=error)

        if password_incorrect:
            error = "As senhas não coincidem."
            return render_template("auth/register.html", error=error)

        # Insere usuário no banco
        database.insert_user(
            name,
            last_name,
            phone,
            zip_code,
            state,
            city,
            neighborhood,
            address,
            house_number,
            email,
            password,
            0,
        )

        # Cria carrinho do usuário
        user = database.select_user(email, password)
        if user:
            database.insert_cart(user[0][0])

        return redirect(url_for("login"))

    return redirect("/register")


@app.route("/user", methods=["GET", "POST"])
def user():
    user_id = session["user_id"]
    user = database.select_user_by_id(user_id)[0]

    return render_template(
        "user/index.html", user=user, is_admin=database.is_admin(user_id)
    )


@app.route("/user/update/<id>", methods=["GET", "POST"])
def update_user(id):
    user = database.select_user_by_id(id)[0]

    if request.method == "POST":
        # Coletar dados do formulário
        name = request.form["name"]
        last_name = request.form["last_name"]
        phone = request.form["phone"]
        email = request.form["email"]
        state = request.form["state"]
        city = request.form["city"]
        zip_code = request.form["zip_code"]
        neighborhood = request.form["neighborhood"]
        address = request.form["address"]
        house_number = request.form["house_number"]
        password = request.form["password"]
        password_c = request.form["password_c"]

        # Verificar se senha foi preenchida
        if password or password_c:
            if password != password_c:
                # Senhas não coincidem
                return render_template(
                    "user/update.html",
                    id=user[0],
                    name=name,
                    last_name=last_name,
                    phone=phone,
                    email=email,
                    state=state,
                    city=city,
                    zip_code=zip_code,
                    neighborhood=neighborhood,
                    address=address,
                    house_number=house_number,
                    user_id=user[0],
                    is_admin=database.is_admin(session["user_id"]),
                    error="As senhas não coincidem!",
                )
            # Se senhas coincidem, usar a nova senha
            update_password = password
        else:
            # Se não preencheu senha, não atualizar a senha
            update_password = None

        # Fazer o update
        database.update_user(
            id=id,
            name=name,
            last_name=last_name,
            phone=phone,
            email=email,
            state=state,
            city=city,
            zip_code=zip_code,
            neighborhood=neighborhood,
            address=address,
            house_number=house_number,
            password=update_password,
        )

        return redirect(url_for("user"))

    return render_template(
        "user/update.html",
        id=user[0],
        name=user[1],
        last_name=user[2],
        phone=user[3],
        email=user[10], 
        state=user[5], 
        city=user[6],  
        zip_code=user[4],  
        neighborhood=user[7],  
        address=user[8],  
        house_number=user[9], 
        password="",
        user_id=user[0],
        is_admin=database.is_admin(session["user_id"]),
    )


@app.route("/user/manage")
def manage_users():
    users = database.get_users()
    is_admin = database.is_admin(session["user_id"])
    users_filtered = [user for user in users if not user[8]]
    return render_template("user/manage.html", users=users_filtered, is_admin=is_admin)


@app.route("/user/delete/<id>", methods=["POST"])
def delete_user(id):
    database.delete_user(id)
    return redirect(url_for("manage_users"))


@app.route("/products", methods=["GET", "POST"])
def products():
    print(session["user_id"])
    return render_template(
        "product/index.html",
        products=database.get_products(),
        is_admin=database.is_admin(session["user_id"]),
    )


@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.route("/product/create", methods=["POST"])
def create_product():
    if request.method == "POST":
        try:
            if "product_img" not in request.files:
                flash("Nenhum arquivo enviado")
                return redirect(request.url)

            file = request.files["product_img"]

            if file.filename == "":
                flash("Nenhuma imagem selecionada")
                return redirect(request.url)

            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

                database.insert_product(
                    request.form["product_name"],
                    request.form["product_desc"],
                    request.form["product_price"],
                    filename,
                )

                flash("Produto criado com sucesso!")
                return redirect(url_for("products"))

        except Exception as e:
            flash(f"Erro: {str(e)}")
            return redirect(request.url)

    return redirect(url_for("products"))


@app.route("/product/update/<int:id>", methods=["GET", "POST"])
def update_product(id):
    product = database.get_product_by_id(id)
    if not product:
        abort(404)

    if request.method == "POST":
        try:
            product_name = request.form["product_name"]
            product_desc = request.form["product_desc"]
            product_price = float(request.form["product_price"])

            filename = product[4] if len(product) > 4 else None

            if "product_img" in request.files:
                file = request.files["product_img"]
                if file and file.filename != "":  # Se a imagem foi fornecida
                    if allowed_file(file.filename):
                        if filename and os.path.exists(
                            os.path.join(app.config["UPLOAD_FOLDER"], filename)
                        ):
                            os.remove(
                                os.path.join(app.config["UPLOAD_FOLDER"], filename)
                            )

                        filename = secure_filename(
                            file.filename
                        )  # Usando o nome original da imagem
                        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                        file.save(file_path)
                    else:
                        flash("Tipo de arquivo não permitido", "error")
                        return redirect(request.url)

            database.update_product(
                id, product_name, product_desc, product_price, filename
            )
            flash("Produto atualizado com sucesso!", "success")
            return redirect(url_for("products"))

        except ValueError:
            flash("Preço inválido", "error")
        except Exception as e:
            flash(f"Erro ao atualizar produto: {str(e)}", "error")

    return render_template(
        "product/update.html",
        product_id=id,
        product_name=product[1],
        product_desc=product[2],
        product_price=product[3],
        product_img=product[4] if len(product) > 4 else None,
        is_admin=database.is_admin(session.get("user_id", 0)),
    )


@app.route("/product/delete/<int:product_id>", methods=["POST"])
def delete_product(product_id):
    if not database.is_admin(session.get("user_id", 0)):
        abort(403)

    try:
        if database.delete_product(product_id):
            flash("Produto deletado com sucesso!", "success")
        else:
            flash("Failed to delete product", "error")
    except Exception as e:
        flash(f"Erro ao deletar produto: {str(e)}", "error")

    return redirect(url_for("products"))


@app.route("/user/select/<id>", methods=["GET", "POST"])
def select_product(id):
    database.select_product(id)
    product = database.get_product_by_id(id)
    return render_template(
        "product/select.html",
        product_id=id,
        product_name=product[1],
        product_desc=product[2],
        product_price=product[3],
        product_img=product[4],
        is_admin=database.is_admin(session["user_id"]),
    )


@app.route("/cart", methods=["GET"])
def cart():
    if "user_id" not in session or session["user_id"] == 0:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    cart_items = database.get_full_cart_items(user_id)

    total_price = sum(item["total_price"] for item in cart_items)

    return render_template(
        "cart/index.html",
        cart_items=cart_items,
        total_price=total_price,
        is_admin=database.is_admin(session["user_id"]),
    )


@app.route("/cart/add/<product_id>", methods=["POST"])
def add_to_cart(product_id):
    if "user_id" not in session or session["user_id"] == 0:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    quantity = int(request.form["quantity"])
    product = database.get_product_by_id(product_id)

    if not product:
        abort(404)

    unit_price = float(product[3])

    cart_id = database.get_cart_id(user_id)
    if not cart_id:
        database.insert_cart(user_id)
        cart_id = database.get_cart_id(user_id)

    existing_item = database.get_cart_item_quantity(cart_id, product_id)

    if existing_item:
        new_quantity = existing_item[1] + quantity
        database.update_cart_item(existing_item[0], new_quantity)
    else:
        database.insert_cart_item(cart_id, product_id, quantity, unit_price)

    return redirect(url_for("cart"))


@app.route("/cart/update/<int:item_id>", methods=["POST"])
def update_cart_item(item_id):
    if "user_id" not in session or session["user_id"] == 0:
        return redirect(url_for("login"))

    quantity = int(request.form["quantity"])

    database.update_cart_item(item_id, quantity)

    return redirect(url_for("cart"))


@app.route("/cart/remove/<int:item_id>", methods=["POST"])
def remove_cart_item(item_id):
    if "user_id" not in session or session["user_id"] == 0:
        return redirect(url_for("login"))

    database.remove_cart_item(item_id)

    return redirect(url_for("cart"))


@app.route("/cart/clear", methods=["POST"])
def clear_cart():
    if "user_id" not in session or session["user_id"] == 0:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    database.clear_cart(user_id)

    return redirect(url_for("cart"))


@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    if "user_id" not in session or session["user_id"] == 0:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    cart_items = database.get_full_cart_items(user_id)
    total_price = sum(item["total_price"] for item in cart_items) if cart_items else 0

    if not cart_items:
        flash("Seu carrinho está vazio", "error")
        return redirect(url_for("cart"))

    if request.method == "POST":
        use_registered = request.form.get("use_registered_address") == "on"

        user_data = database.select_user_by_id(user_id)[0]
        if use_registered:
            shipping_data = {
                "address": user_data[7] if len(user_data) > 7 else "Não cadastrado",
                "house_number": user_data[8] if len(user_data) > 8 else "",
                "city": user_data[5],
                "state": user_data[4],
                "zip_code": user_data[6] if len(user_data) > 6 else "",
            }
        else:
            shipping_data = {
                "address": request.form.get("new_address", "Não informado"),
                "house_number": request.form.get("new_house_number", ""),
                "city": request.form.get("new_city", "Não informado"),
                "state": request.form.get("new_state", "Não informado"),
                "zip_code": request.form.get("new_zipcode", ""),
            }

        try:
            # Alterar para None em vez de gerar código automático
            database.insert_order(
                tracking_code=None,  # Agora é None
                user_id=user_id,
                order_date=datetime.now(),
                total_price=total_price,
                confirmed_payment=0,
                shipped=0,
                completed=0,
                shipping_address=shipping_data["address"],
                shipping_house_number=shipping_data["house_number"],
                shipping_city=shipping_data["city"],
                shipping_state=shipping_data["state"],
                shipping_zip_code=shipping_data["zip_code"],
                payment_status="pendente",  # Adicionar este parâmetro
                shipping_status="pendente",  # Adicionar este parâmetro
            )

            database.clear_cart(user_id)

            flash("Pedido finalizado com sucesso!", "success")
            return redirect(url_for("checkout_success"))

        except Exception as e:
            flash(f"Erro ao finalizar compra: {str(e)}", "error")
            return redirect(url_for("cart"))

    user = database.select_user_by_id(user_id)[0]
    return render_template(
        "cart/checkout.html",
        user=user,
        cart_items=cart_items,
        total_price=total_price,
        is_admin=database.is_admin(session["user_id"]),
    )


@app.route("/process-payment", methods=["POST"])
def process_payment():
    try:
        user_id = session["user_id"]
        cart_items = database.get_full_cart_items(user_id)

        if not cart_items:
            flash("Seu carrinho está vazio", "error")
            return redirect(url_for("cart"))

        total_price = sum(item["price"] * item["quantity"] for item in cart_items)

        order_id = database.insert_order_and_get_id(
            tracking_code=None,
            user_id=user_id,
            total_price=total_price,
            shipping_address=request.form.get("new_address"),
            shipping_house_number=request.form.get("new_house_number"),
            shipping_city=request.form.get("new_city"),
            shipping_state=request.form.get("new_state"),
            shipping_zip_code=request.form.get("new_zipcode"),
        )

        if not order_id:
            raise Exception("Falha ao criar pedido")

        for item in cart_items:
            database.insert_order_item(
                order_id=order_id,
                product_id=item["product_id"],
                quantity=item["quantity"],
                price=item["price"],
            )

        database.clear_cart(user_id)

        flash("Pagamento processado com sucesso!", "success")
        return redirect(url_for("my_orders"))

    except Exception as e:
        logger.error(f"Erro no pagamento: {str(e)}")
        flash(f"Erro ao processar pagamento: {str(e)}", "error")
        return redirect(url_for("cart"))


@app.route("/checkout/success")
def checkout_success():
    if "user_id" not in session or session["user_id"] == 0:
        return redirect(url_for("login"))

    return render_template(
        "cart/checkout_success.html", is_admin=database.is_admin(session["user_id"])
    )


@app.route("/confirmation/<tracking_code>")
def order_confirmation(tracking_code):
    if "user_id" not in session or session["user_id"] == 0:
        return redirect(url_for("login"))

    return render_template(
        "order/confirmation.html",
        tracking_code=tracking_code,
        is_admin=database.is_admin(session["user_id"]),
    )


@app.route("/orders")
def my_orders():
    if "user_id" not in session or session["user_id"] == 0:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    orders = database.get_user_orders(user_id)

    return render_template(
        "order/my_orders.html",
        orders=orders,
        is_admin=database.is_admin(session["user_id"]),
    )


@app.route("/admin/orders")
def admin_orders():
    if not database.is_admin(session.get("user_id", 0)):
        abort(403)

    status_filter = request.args.get("status", "all")
    search_query = request.args.get("search", "")

    orders = database.get_all_orders(
        status_filter=status_filter, search_query=search_query
    )

    print(orders)

    return render_template(
        "admin/orders.html",
        orders=orders,
        status_filter=status_filter,
        search_query=search_query,
        is_admin=True,
    )


@app.route("/admin/order/<int:order_id>", methods=["GET", "POST"])
def admin_order_detail(order_id):
    if not database.is_admin(session.get("user_id", 0)):
        abort(403)

    if request.method == "POST":
        shipping_status = request.form.get("shipping_status")
        payment_status = request.form.get("payment_status")
        tracking_code = request.form.get("tracking_code", "").strip() or None

        try:
            database.update_order_status(
                order_id, shipping_status, payment_status, tracking_code
            )
            flash("Status atualizado com sucesso!", "success")
        except Exception as e:
            print(f"ERRO no update: {e}")
            flash(f"Erro ao atualizar status: {e}", "error")

    order, order_items = database.get_order_details(order_id)
    if not order:
        abort(404)

    return render_template(
        "admin/order_detail.html", order=order, order_items=order_items, is_admin=True
    )


@app.route("/admin/order/update_status", methods=["POST"])
def update_order_status():
    """Endpoint para atualização de status via AJAX (opcional)"""
    if not database.is_admin(session.get("user_id", 0)):
        return jsonify({"success": False, "error": "Acesso negado"}), 403

    try:
        data = request.get_json()
        order_id = data["order_id"]
        new_status = data["status"]

        database.update_shipping_status(order_id, new_status)

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/about")
def about():

    info = database.get_about()

    social_media_tuples = database.get_social_media()

    social_media = []
    for social in social_media_tuples:
        social_media.append(
            {"id": social[0], "social_name": social[1], "social_link": social[2]}
        )

    return render_template(
        "about/index.html",
        info=info,
        social_media=social_media,
        is_admin=database.is_admin(session.get("user_id", 0)),
    )


@app.route("/admin/about/edit", methods=["GET", "POST"])
def about_edit():

    current_info = database.get_about()

    social_media_tuples = database.get_social_media()

    social_media = []
    for social in social_media_tuples:
        social_media.append(
            {"id": social[0], "social_name": social[1], "social_link": social[2]}
        )

    if request.method == "POST":
        new_title = request.form["title"].strip()
        new_content = request.form["content"].strip()

        title = new_title if new_title else current_info['title']
        content = new_content if new_content else current_info['content']

        database.update_about(title, content)

        social_names = request.form.getlist("social_name[]")
        social_links = request.form.getlist("social_link[]")

        database.delete_social_media()

        for name, link in zip(social_names, social_links):
            if name and link:
                database.insert_social_media(name, link)

        flash("Alterações salvas com sucesso!", "success")
        return redirect(url_for("about"))

    info_dict = {
        "title": current_info['title'] if current_info else "",
        "content": current_info['content'] if current_info else "",
    }

    return render_template("about/edit.html", info=info_dict, social_media=social_media)


@app.route("/admin/social-media/delete/<int:id>")
def delete_social_media(id):
    database.delete_social_media_by_id(id)
    flash("Rede social removida com sucesso!", "success")
    return redirect(url_for("about_edit"))


if __name__ == "__main__":
    app.run("localhost", debug=False)
