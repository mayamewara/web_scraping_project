from flask import Flask, render_template, request, jsonify
from flask_cors import CORS, cross_origin
import requests
from bs4 import BeautifulSoup as bs
import logging
import pymongo

logging.basicConfig(filename="scraper.log", level=logging.INFO)

app = Flask(__name__)

@app.route('/', methods=["GET"])
def homepage():
    return render_template("index.html")

@app.route("/review", methods=["POST", "GET"])
def index():
    if request.method == 'POST':
        try:
            searchString = request.form['content'].replace(" ", "")
            flipkart_url = "https://www.flipkart.com/search?q=" + searchString

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.5",
            }

            cookies = {
                "cookie_name": "cookie_value",
            }

            response = requests.get(flipkart_url, headers=headers, cookies=cookies, verify=False)

            if response.status_code == 200:
                print("Request successful!")
                page_content = response.text

                with open("flipkart_iphone12pro.html", "w", encoding="utf-8") as file:
                     file.write(response.text)

                # Then read the file to parse it
                with open("flipkart_iphone12pro.html", "r", encoding="utf-8") as file:
                    saved_content = file.read()     


                flipkart_html = bs(saved_content, "html.parser")
                bigboxes = flipkart_html.findAll("div", {"class": "cPHDOP col-12-12"})
                del bigboxes[0:3]
                box = bigboxes[0]

                productlink = "https://www.flipkart.com" + bigboxes[3].div.div.div.a["href"]
                prod_req = requests.get(productlink, headers=headers, cookies=cookies, verify=False)
                prod_html = bs(prod_req.text, "html.parser")
                print(prod_html)
                comment_box = prod_html.findAll("div", {"class": "RcXBOT"})

                filename = searchString + ".csv"
                fw =  open(filename, "w")
                headers = "product, Customer Name, Rating, Heading, Comment\n"
                fw.write(headers)
                reviews = []

                for commentbox in comment_box:
                    try:
                        name = commentbox.div.div.find_all('p', {"class": "_2NsDsF AwS1CA"})[0].text
                    except:
                        logging.info('name')

                    try:
                        rating = commentbox.div.div.div.div.text
                    except:
                        rating = 'no rating'
                        logging.info("rating")

                    try:
                        commentHead = commentbox.div.div.div.p.text
                    except:
                        commentHead = 'no comment Heading'
                        logging.info(commentHead)

                    try:
                        cont = commentbox.div.div.findAll("div", {"class": ""})
                        custComment = cont[0].div.text
                    except Exception as e:
                        logging.info(e)
                        

                    mydict = {"product": searchString, "Name": name, "Rating": rating, "CommentHead": commentHead, "comment": custComment}
                    reviews.append(mydict)
                logging.info("log my final result {}".format(reviews))    
                     
                client = pymongo.MongoClient("mongodb+srv://pwskills:prakash@cluster0.wjepz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
                db = client["review_scrap"]
                review_col = db['review_scrap_data']
                review_col.insert_many(reviews)


            return render_template('result.html', reviews=reviews[0:(len(reviews)-1)])
        except Exception as e:
            logging.info(e)
            return 'Something went wrong'
    else:
        return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True,port=5001)
