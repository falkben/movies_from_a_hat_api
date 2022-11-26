module Pages.Movies.Search exposing (Model, Msg, page)

import Api exposing (Movie)
import Auth
import Effect exposing (Effect)
import Html exposing (Html, div, h1, h2, img, text)
import Html.Attributes exposing (src)
import Html.Events exposing (onClick)
import Http
import Page exposing (Page)
import RemoteData exposing (RemoteData(..), WebData)
import Route exposing (Route)
import Shared
import Ui exposing (font)
import View exposing (View)


page : Auth.User -> Shared.Model -> Route () -> Page Model Msg
page _ _ _ =
    Page.new
        { init = init
        , update = update
        , subscriptions = subscriptions
        , view = view
        }



-- INIT


type alias Model =
    { query : String
    , results : WebData (List Movie)
    }


init : () -> ( Model, Effect Msg )
init () =
    ( { query = "", results = NotAsked }
    , Effect.none
    )



-- UPDATE


type Msg
    = QueryInput String
    | Search
    | SearchResult (Result Http.Error (List Movie))


update : Msg -> Model -> ( Model, Effect Msg )
update msg model =
    case msg of
        QueryInput query ->
            ( { model | query = query }, Effect.none )

        Search ->
            ( { model | results = Loading }, Api.searchMovies model.query SearchResult )

        SearchResult (Ok movies) ->
            ( { model | results = Success movies }, Effect.none )

        SearchResult (Err err) ->
            ( { model | results = Failure err }, Effect.none )



-- SUBSCRIPTIONS


subscriptions : Model -> Sub Msg
subscriptions _ =
    Sub.none



-- VIEW


view : Model -> View Msg
view model =
    { title = "Search for Movies"
    , body =
        [ h1 [ font.heading ] [ text "Movie Search" ]
        , searchView model
        , resultsView model
        ]
    }


searchView : Model -> Html Msg
searchView model =
    div []
        [ h2 [ font.heading ] [ text "Query" ]
        , Ui.input []
            { label = text "Search"
            , value = model.query
            , onInput = QueryInput
            }
        , Ui.button [ onClick Search ] [ text "Search" ]
        ]


resultsView : Model -> Html Msg
resultsView model =
    div []
        [ h2 [ font.heading ] [ text "Results" ]
        , case model.results of
            NotAsked ->
                text ""

            Loading ->
                text "Loading..."

            Success movies ->
                resultList movies

            Failure _ ->
                text "Oops: Something went wrong"
        ]


resultList : List Movie -> Html Msg
resultList movies =
    div []
        (if List.isEmpty movies then
            [ text "No Results" ]

         else
            List.map movieView movies
        )


movieView : Movie -> Html Msg
movieView movie =
    div []
        [ text movie.title
        , div []
            [ img [ src movie.posterUrl ] []
            ]
        ]
