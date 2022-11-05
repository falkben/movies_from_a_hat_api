module Pages.SignIn exposing (Model, Msg, page)

import Effect exposing (Effect)
import Html exposing (div, h1, input, label, text)
import Html.Attributes exposing (type_, value)
import Html.Events exposing (onInput)
import Page exposing (Page)
import Route exposing (Route)
import Shared
import View exposing (View)


page : Shared.Model -> Route () -> Page Model Msg
page _ _ =
    Page.new
        { init = init
        , update = update
        , subscriptions = subscriptions
        , view = view
        }



-- INIT


type alias Model =
    { username : String
    , password : String
    }


init : () -> ( Model, Effect Msg )
init () =
    ( { username = "", password = "" }
    , Effect.none
    )



-- UPDATE


type Msg
    = UsernameInput String
    | PasswordInput String


update : Msg -> Model -> ( Model, Effect Msg )
update msg model =
    case msg of
        UsernameInput username ->
            ( { model | username = username }, Effect.none )

        PasswordInput password ->
            ( { model | password = password }, Effect.none )



-- SUBSCRIPTIONS


subscriptions : Model -> Sub Msg
subscriptions _ =
    Sub.none



-- VIEW


view : Model -> View Msg
view model =
    { title = "Sign In"
    , body =
        [ h1 [] [ text "Movies From A Hat" ]
        , div []
            [ label []
                [ div [] [ text "Username" ]
                , input [ value model.username, onInput UsernameInput, type_ "text" ] []
                ]
            , label []
                [ div [] [ text "Password" ]
                , input [ value model.password, onInput PasswordInput, type_ "text" ] []
                ]
            ]
        ]
    }
