%% select_shape_parameters - Shape Selection UI for Circle and Rectangle
% 
% Description:
%   This function creates a graphical user interface (UI) that allows the user
%   to select between two geometric shapes: a Circle or a Rectangle. The user
%   can specify the dimensions (radius for Circle, width and height for Rectangle),
%   as well as the center coordinates (xCenter, yCenter) for either shape.
%   The function waits until the user confirms their selection by clicking the
%   "Confirm" button, and then returns the selected parameters to the calling script.
%
% Inputs:
%   None (this function does not accept any input arguments).
%
% Outputs:
%   - isCircle (logical): A boolean flag indicating whether the Circle shape
%     was selected (true = Circle selected, false = Circle not selected).
%
%   - isRectangle (logical): A boolean flag indicating whether the Rectangle shape
%     was selected (true = Rectangle selected, false = Rectangle not selected).
%
%   - radius (numeric): The radius of the selected Circle (in cm). This value
%     is only meaningful if the Circle is selected. If not selected, the radius
%     will be returned as 0.
%
%   - width (numeric): The width of the selected Rectangle (in cm). This value
%     is only meaningful if the Rectangle is selected. If not selected, the width
%     will be returned as 0.
%
%   - height (numeric): The height of the selected Rectangle (in cm). This value
%     is only meaningful if the Rectangle is selected. If not selected, the height
%     will be returned as 0.
%
%   - xCenter (numeric): The X-coordinate of the center of the selected shape
%     (in cm). This value is applicable for both shapes (Circle or Rectangle).
%
%   - yCenter (numeric): The Y-coordinate of the center of the selected shape
%     (in cm). This value is applicable for both shapes (Circle or Rectangle).
%
% User Interface (UI) Elements:
%   - A checkbox for selecting the Circle shape and an input field for entering
%     the radius.
%
%   - A checkbox for selecting the Rectangle shape and input fields for entering
%     the width and height.
%
%   - Input fields for entering the X and Y coordinates of the shape's center.
%
%   - A "Confirm" button to finalize the selection and close the UI.
%
% Behavior:
%   - If the user selects neither the Circle nor the Rectangle, the function will
%     display an error message and stop further execution.
%   - The function pauses the execution of the calling script using "uiwait"
%     until the UI figure is closed.
%
% Example Usage:
%   % In the main script:
%   [isCircle, isRectangle, radius, width, height, xCenter, yCenter] = select_shape_parameters();
%
%   % Example of handling the returned values:
%   if isCircle
%       disp(['Circle selected with radius: ', num2str(radius), ' cm']);
%   elseif isRectangle
%       disp(['Rectangle selected with width: ', num2str(width), ' cm and height: ', num2str(height), ' cm']);
%   end
%
%   disp(['Center coordinates: (', num2str(xCenter), ', ', num2str(yCenter), ')']);
%
% Notes:
%   - The figure uses the golden ratio (phi ≈ 1.618) for aesthetic proportions.
%   - The UI waits for user interaction until the "Confirm" button is pressed.
%   - The function stops script execution with an error if no shape is selected.
%
% Author: [Matthieu Roblin & Luis Saluden]
% Date: [2024-10-19]
% Version: 1.0


function [isCircle, isRectangle, radius, width, height, xCenter, yCenter] = select_shape_parameters()
    % Initialize shared variables
    isCircle = false;
    isRectangle = false;
    radius = 0;
    width = 0;
    height = 0;
    xCenter = 0;
    yCenter = 0;
    phi = 1.618;

    figureHeight = 400;
    figureWidth = phi * figureHeight;

    % Create the main figure
    shapeFig = uifigure('Position', [100 100 figureWidth figureHeight], 'Name', 'Select Shape and Parameters');

    % Panel for Circle on the left
    circlePanelWidth = 0.45 * figureWidth; % 45% of the figure width
    circlePanelHeight = figureHeight / (phi^2); % 35% of the figure height
    circlePanelX = 20;
    circlePanelY = 200;
    circlePanel = uipanel(shapeFig, 'Title', 'Circle', 'Position', [circlePanelX circlePanelY circlePanelWidth circlePanelHeight]);

    % Checkbox for Circle
    checkboxWidth = 100;
    checkboxHeight = 20;
    circleCheckbox = uicheckbox(circlePanel, 'Text', 'Select Circle', 'Position', [20 circlePanelHeight-60 checkboxWidth checkboxHeight]);

    % Input for radius
    radiusLabelWidth = 80;
    radiusLabelHeight = 20;
    uilabel(circlePanel, 'Text', 'Radius (cm):', 'Position', [20 circlePanelHeight-100 radiusLabelWidth radiusLabelHeight]);
    radiusField = uieditfield(circlePanel, 'numeric', 'Position', [120 circlePanelHeight-100 80 20], 'Enable', 'On', 'Value', radius);

    % Panel for Rectangle on the right
    gapPanel = 20;
    rectPanelX = circlePanelX + circlePanelWidth + gapPanel;
    rectPanelY = circlePanelY;
    rectPanelWidth = circlePanelWidth;
    rectPanelHeight = circlePanelHeight;
    rectPanel = uipanel(shapeFig, 'Title', 'Rectangle', 'Position', [rectPanelX rectPanelY rectPanelWidth rectPanelHeight]);

    % Checkbox for Rectangle
    rectangleCheckbox = uicheckbox(rectPanel, 'Text', 'Select Rectangle', 'Position', [20 rectPanelHeight-60 checkboxWidth*1.5 checkboxHeight]);

    % Input for width
    uilabel(rectPanel, 'Text', 'Width (cm):', 'Position', [20 rectPanelHeight-100 radiusLabelWidth radiusLabelHeight]);
    widthField = uieditfield(rectPanel, 'numeric', 'Position', [120 rectPanelHeight-100 80 20], 'Enable', 'On', 'Value', width);

    % Input for height
    uilabel(rectPanel, 'Text', 'Height (cm):', 'Position', [20 rectPanelHeight-140 radiusLabelWidth radiusLabelHeight]);
    heightField = uieditfield(rectPanel, 'numeric', 'Position', [120 rectPanelHeight-140 80 20], 'Enable', 'On', 'Value', height);

    % Panel for Center coordinates below both columns
    centerPanelWidth = circlePanelWidth + rectPanelWidth + gapPanel;
    centerPanelHeight = (figureHeight - circlePanelHeight) / (phi^2);
    centerPanelX = 20;
    centerPanelY = 80;
    centerPanel = uipanel(shapeFig, 'Title', 'Center coordinates', 'Position', [centerPanelX centerPanelY centerPanelWidth centerPanelHeight]);

    % Input for xCenter
    uilabel(centerPanel, 'Text', 'xCenter:', 'Position', [centerPanelX*(phi^2) 20 60 20]);
    xCenterField = uieditfield(centerPanel, 'numeric', 'Position', [centerPanelX*(phi^2)+60 20 80 20], 'Value', xCenter);

    % Input for yCenter
    uilabel(centerPanel, 'Text', 'yCenter:', 'Position', [(centerPanelX+centerPanelWidth)/(phi^2) 20 60 20]);
    yCenterField = uieditfield(centerPanel, 'numeric', 'Position', [60+(centerPanelX+centerPanelWidth)/(phi^2) 20 80 20], 'Value', yCenter);

    % Confirm button
    confirmButtonWidth = 100;
    confirmButtonHeight = 30;
    confirmButtonX = (figureWidth - confirmButtonWidth) / 2;
    confirmButtonY = 20;
    uibutton(shapeFig, 'Text', 'Confirm', 'Position', [confirmButtonX confirmButtonY confirmButtonWidth confirmButtonHeight], ...
        'ButtonPushedFcn', @(btn, event) onConfirmButtonPushed(circleCheckbox, rectangleCheckbox, xCenterField, yCenterField, widthField, heightField, radiusField, shapeFig));

    % Wait for the figure to be closed
    uiwait(shapeFig);

    % Callback function for the Confirm button
    function onConfirmButtonPushed(circleCheckbox, rectangleCheckbox, xCenterField, yCenterField, widthField, heightField, radiusField, shapeFig)
        % Retrieve the values from the UI elements
        isCircle = circleCheckbox.Value;
        isRectangle = rectangleCheckbox.Value;
        xCenter = xCenterField.Value;
        yCenter = yCenterField.Value;
        width = widthField.Value;
        height = heightField.Value;
        radius = radiusField.Value;

        % Close the shape selection figure
        close(shapeFig);

        % Check if neither Circle nor Rectangle is selected
        if ~isCircle && !isRectangle
            msgbox('No object selected. Stopping script execution.', 'Error', 'error');
            error('No object selected.');
        end
    end
end
