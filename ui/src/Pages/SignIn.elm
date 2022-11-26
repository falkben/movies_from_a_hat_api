module Pages.SignIn exposing (Model, Msg, page)

import Effect exposing (Effect)
import Html exposing (h1, text)
import Html.Attributes exposing (autofocus, class)
import Page exposing (Page)
import Route exposing (Route)
import Shared
import Ui exposing (button, centerXY, formColumn, input, password, font)
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
        [ centerXY [ class "-mt-24" ]
            [ h1 [ font.heading, class "text-3xl mb-8" ]
                [ text "Movies From A Hat" ]
            , formColumn []
                [ input [ autofocus True, class "w-full" ]
                    { label = text "Username"
                    , value = model.username
                    , onInput = UsernameInput
                    }
                , password [ class "w-full" ]
                    { label = text "Password"
                    , value = model.password
                    , onInput = PasswordInput
                    }
                , button [] [ text "Sign In" ]
                ]
            ]
        ]
    }
