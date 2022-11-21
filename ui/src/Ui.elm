module Ui exposing
    ( row, column, centerXY
    , centerContent
    , input, password, button
    , formColumn
    , font, debug
    )

{-| Thiss module contains functions for rendering views in a consistent way. You
can think of it as the root of the design system for the app.


# Layout

@docs row, column, centerXY

@docs centerContent


# Forms

@docs input, password, button

@docs formColumn


# Utilities

@docs style, debug

-}

import Html exposing (Attribute, Html, div, label)
import Html.Attributes exposing (autocomplete, class, type_)


{-| Reusable utility styles
-}
font : { default : Attribute msg, heading : Attribute msg }
font =
    { default = class "bg-gray text-white h-full font-mitr"
    , heading = class "font-righteous uppercase"
    }



-- LAYOUT


{-| A column layout. Items are stacked top to bottom.
-}
column : List (Attribute msg) -> List (Html msg) -> Html msg
column attrs content =
    div (class "flex flex-col" :: attrs) content


{-| A row layout. Items are stacked left-to-right.
-}
row : List (Attribute msg) -> List (Html msg) -> Html msg
row attrs content =
    div (class "flex flex-row" :: attrs) content


{-| Centers content horizontally and vertically
-}
centerXY : List (Attribute msg) -> List (Html msg) -> Html msg
centerXY attrs content =
    row [ class "h-full items-center", centerContent ]
        [ div attrs content ]


{-| Causes a row or column to center it's content
-}
centerContent : Attribute msg
centerContent =
    class "justify-center"



-- FORMS


{-| A plain text input
-}
input :
    List (Attribute msg)
    ->
        { label : Html msg
        , value : String
        , onInput : String -> msg
        }
    -> Html msg
input attrs opts =
    label []
        [ Html.input (type_ "text" :: textInputStyle :: attrs)
            []
        , div [ textLabelStyle ] [ opts.label ]
        ]


{-| A password input
-}
password :
    List (Attribute msg)
    ->
        { label : Html msg
        , value : String
        , onInput : String -> msg
        }
    -> Html msg
password attrs opts =
    label []
        [ Html.input
            (type_ "password" :: autocomplete True :: textInputStyle :: attrs)
            []
        , div [ textLabelStyle ] [ opts.label ]
        ]


textInputStyle : Attribute msg
textInputStyle =
    class """
bg-transparent border-b-2 border-solid border-white mb-1 px-1
focus:outline-none focus:bg-primary
"""


textLabelStyle : Attribute msg
textLabelStyle =
    class "pl-1"


button : List (Attribute msg) -> List (Html msg) -> Html msg
button attrs content =
    Html.button
        (class "bg-primary text-white"
            :: class "focus-visible:ring ring-secondary focus:outline-none"
            :: class "rounded py-1"
            :: attrs
        )
        content


{-| A column, but configured to make spacing look nice for a series of form
fields.
-}
formColumn : List (Attribute msg) -> List (Html msg) -> Html msg
formColumn attrs content =
    column (class "space-y-4" :: attrs)
        content



-- UTILITY


{-| Draws a line around an element so you can check it's layout more closely
-}
debug : Attribute msg
debug =
    class "border-2 border-solid outline-1 outline-offset-0 outline-blue"
