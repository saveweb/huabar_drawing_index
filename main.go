package main

import (
	"context"
	"database/sql"
	"encoding/csv"
	"fmt"
	"os"
	"strconv"
	"strings"

	"github.com/gin-gonic/gin"

	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/bson/primitive"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"

	_ "github.com/mattn/go-sqlite3"
)

type JidAuthorName struct {
	Jid  string
	Name string
}

var MONGODB_URI string = os.Getenv("MONGODB_URI")

const MONGO_DB_NAME string = "huabar"

// var mongoClient *mongo.Client
var notes_collection *mongo.Collection

var sql_db *sql.DB

var jidAuthorNameMap = make(map[JidAuthorName]bool)

// The init function will run before our main function to establish a connection to MongoDB. If it cannot connect it will fail and the program will exit.
func init() {
	go load_data()
	go connect_to_sqlite()
	go connect_to_mongodb()
}

func connect_to_sqlite() {
	// "huabar_draws.db"
	fmt.Println("Connecting to SQLite...")
	_db, err := sql.Open("sqlite3", "db/huabar_draws.db")
	sql_db = _db
	if err != nil {
		panic(err)
	}
	// table: huabar_draws
	// schema: file_key, zipname

	count := 0
	// how many rows in the table
	rows, err := sql_db.Query("SELECT COUNT(*) FROM huabar_draws")
	if err != nil {
		panic(err)
	}
	for rows.Next() {
		rows.Scan(&count)
	}
	fmt.Println(count)
	fmt.Println("Connected to SQLite!")
}

func get_zipname_by_file_key(file_key string) (*string, error) {
	var zipname *string = nil
	row := sql_db.QueryRow("SELECT zipname FROM huabar_draws WHERE file_key = ?", file_key)
	err := row.Scan(&zipname)
	if err != nil {
		return nil, err
	}
	return zipname, nil
}

func connect_to_mongodb() {
	fmt.Println("Connecting to MongoDB...")
	serverAPI := options.ServerAPI(options.ServerAPIVersion1)
	opts := options.Client().ApplyURI(MONGODB_URI).SetServerAPIOptions(serverAPI)

	client, err := mongo.Connect(context.TODO(), opts)
	if err != nil {
		panic(err)
	}
	err = client.Ping(context.TODO(), nil)
	// mongoClient = client
	notes_collection = client.Database(MONGO_DB_NAME).Collection("notes")

	if err != nil {
		panic(err)
	}
	fmt.Println("Connected to MongoDB!")
}

func load_data() {
	fmt.Println("Loading data...")
	file, err := os.Open("jid_authorname_map/jid_authorname_maped.csv")
	if err != nil {
		panic(err)
	}
	defer file.Close()

	reader := csv.NewReader(file)
	for {
		record, err := reader.Read()
		if err != nil {
			break
		}
		jidAuthorNameMap[JidAuthorName{Jid: record[0], Name: record[1]}] = true
	}
	fmt.Println(len(jidAuthorNameMap))
	fmt.Println("Data loaded!")
}

func search_authorname(q string, limit int, TYPE string) ([]JidAuthorName, error) {
	var results []JidAuthorName
	if TYPE == "like" {
		for jidAuthorName := range jidAuthorNameMap {
			if strings.Contains(jidAuthorName.Name, q) {
				if len(results) >= limit {
					break
				}
				results = append(results, jidAuthorName)
			}
		}
	} else if TYPE == "equal" {
		for jidAuthorName := range jidAuthorNameMap {
			if jidAuthorName.Name == q {
				if len(results) >= limit {
					break
				}
				results = append(results, jidAuthorName)
			}
		}
	} else {
		return nil, fmt.Errorf("invalid type")
	}

	return results, nil
}

func main() {
	r := gin.Default()
	// results := search_authorname_like("耑江古木")
	// zeg97iab-0@zhizhiyaya.com/HuaLiao
	r.GET("/api/search", func(c *gin.Context) {
		q := c.Query("q")
		limitStr := c.Query("limit")
		TYPE := c.Query("type")

		limit, err := strconv.Atoi(limitStr)
		if err != nil {
			limit = 100
		}
		if TYPE == "" {
			TYPE = "like"
		}
		if TYPE != "like" && TYPE != "equal" {
			c.JSON(400, gin.H{"error": "invalid type"})
			return
		}

		results, err := search_authorname(q, limit, TYPE)
		if err != nil {
			c.JSON(500, gin.H{"error": err.Error()})
			return
		}
		c.JSON(200, results)
	})

	r.GET("/api/get_zipname", func(c *gin.Context) {
		key := c.Query("key")
		zipname, err := get_zipname_by_file_key(key)
		if err != nil {
			c.JSON(500, gin.H{"error": err.Error()})
			return
		}
		c.JSON(200, gin.H{"zipname": zipname})
	})

	r.GET("/api/notes", func(c *gin.Context) {
		jid := c.Query("jid")
		if jid == "" {
			c.JSON(400, gin.H{"error": "jid is required"})
			return
		}

		var notes []primitive.M = make([]primitive.M, 0)
		cur, err := notes_collection.Find(context.Background(), bson.M{"payload.jid": jid})
		if err != nil {
			c.JSON(500, gin.H{"error": err.Error()})
			return
		}
		defer cur.Close(context.Background())

		for cur.Next(context.Background()) {
			var note primitive.M
			err := cur.Decode(&note)
			if err != nil {
				c.JSON(500, gin.H{"error": err.Error()})
				return
			}
			notes = append(notes, note)
		}

		if err := cur.Err(); err != nil {
			c.JSON(500, gin.H{"error": err.Error()})
			return
		}

		c.JSON(200, notes)
	})

	r.Run()
}
