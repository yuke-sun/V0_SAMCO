import polars as pl
import pandas as pd
from datetime import date
import matplotlib.pyplot as plt
from pandasql import sqldf

##################################
###########Parameters#############
##################################
Starting_Date = date(2019, 3, 18)
Upper_Limit = 1.15
Lower_Limit = 0.50
Percentage = 0.85
Left_Limit = 0.80
Right_Limit = 0.90

Excel_Recap = False
Output_File = r"C:\Users\lbabbi\OneDrive - ISS\Desktop\Projects\SAMCO\V0_SAMCO\Output\TopPercentage_Report.xlsx"

##################################
###########MatplotLib#############
##################################

def Curve_Plotting(TopPercentage, temp_Country, Lower_GMSR, Upper_GMSR):
    # Convert the necessary columns to numpy arrays for plotting
    X_Axis = TopPercentage.select("CumWeight_Cutoff").to_numpy().flatten()
    Y_Axis = TopPercentage.select("Full_MCAP_USD_Cutoff_Company").to_numpy().flatten()

    # Convert temp_Country to numpy arrays for plotting
    X_Axis_Temp = temp_Country.select("CumWeight_Cutoff").to_numpy().flatten()
    Y_Axis_Temp = temp_Country.select("Full_MCAP_USD_Cutoff_Company").to_numpy().flatten()

    # Create the plot
    plt.figure(figsize=(12, 8))
    plt.plot(X_Axis, Y_Axis, marker='o', linestyle='-', color='b')
    plt.plot(X_Axis_Temp, Y_Axis_Temp, linestyle='-', linewidth = 0.5, color='black', label='Temp Country') 

    # Add horizontal lines for Lower_GMSR and Upper_GMSR
    plt.axhline(y=Lower_GMSR, color='r', linestyle='solid', label=f'Lower GMSR = {Lower_GMSR}')
    plt.axhline(y=Upper_GMSR, color='g', linestyle='dotted', label=f'Upper GMSR = {Upper_GMSR}')

    # Add vertical lines at 80%, 85%, and 90%
    plt.axvline(x=0.80, color='orange', linestyle='--', label='80%')
    plt.axvline(x=0.85, color='purple', linestyle='--', label='85%')
    plt.axvline(x=0.90, color='cyan', linestyle='--', label='90%')

    # Adjust limits as needed
    plt.xlim(0, 1.0)  

    # Add labels and title
    plt.xlabel("Cumulative Weight (Cutoff)")
    plt.ylabel("Full MCAP USD (Cutoff)")
    plt.title("Cumulative Weight vs Full MCAP USD Cutoff")

    # Disable scientific notation on y-axis
    plt.ticklabel_format(style='plain', axis='y')

    # Optionally, format y-axis tick labels with commas
    plt.gca().get_yaxis().set_major_formatter(plt.matplotlib.ticker.StrMethodFormatter('{x:,.0f}'))

    # Add label for the last point
    last_x = X_Axis[-1]
    last_y = Y_Axis[-1]
    label = f"Full MCAP: {last_y:,.0f}\nCumWeight: {last_x:.2%}"

    # Adjust the label and arrow to be above the last point for better visibility
    plt.text(last_x, last_y * 5.45, label, fontsize=9, verticalalignment='bottom', horizontalalignment='right', color='black')

    # Adjust the arrow to point from the middle of the label to the actual point
    plt.annotate('', xy=(last_x, last_y), xytext=(last_x, last_y * 5.5),
                 arrowprops=dict(facecolor='black', arrowstyle='->', connectionstyle='arc3,rad=0.3'))

    plt.grid(False)
    plt.tight_layout()
    # Save the figure
    chart_file = f"chart_{TopPercentage['Date'][0]}_{TopPercentage['Country'][0]}.png"
    plt.savefig(chart_file)
    plt.close()  # Close the plot to free up memory
    return chart_file

##################################
##Minimum FreeFloatCountry Level##
##################################

def Minimum_FreeFloat_Country(TopPercentage, Lower_GMSR, Upper_GMSR):
    # Check if last Company Full_MCAP_USD_Cutoff_Company is in between Upper and Lower GMSR

    # Case inside the box
    if (TopPercentage.tail(1).select("Full_MCAP_USD_Cutoff_Company").to_numpy()[0][0] <= Upper_GMSR) & (TopPercentage.tail(1).select("Full_MCAP_USD_Cutoff_Company").to_numpy()[0][0] >= Lower_GMSR):
    
        # Country_GMSR is the Full_MCAP_USD_Cutoff_Company / 2
        Country_GMSR = TopPercentage.tail(1).select("Full_MCAP_USD_Cutoff_Company").to_numpy()[0][0] / 2

        # Check which Companies are below the Country_GMSR
        TopPercentage = TopPercentage.with_columns(
            pl.when(pl.col("Free_Float_MCAP_USD_Cutoff_Company") < Country_GMSR)
            .then(True)
            .otherwise(None)
            .alias("Shadow_Company")
        )

    # Case above the box
    elif (TopPercentage.tail(1).select("Full_MCAP_USD_Cutoff_Company").to_numpy()[0][0] > Upper_GMSR):

        # Country_GMSR is the Upper_GMSR / 2
        Country_GMSR = Upper_GMSR / 2

        # Check which Companies are below the Country_GMSR
        TopPercentage = TopPercentage.with_columns(
            pl.when(pl.col("Free_Float_MCAP_USD_Cutoff_Company") < Country_GMSR)
            .then(True)
            .otherwise(None)
            .alias("Shadow_Company")
        )

    # Return the Frame
    return TopPercentage

##################################
#Read Developed/Emerging Universe#
##################################

# Select columns to read from the Parquets
Columns = ["Date", "Index_Symbol", "Index_Name", "Internal_Number", "ISIN", "SEDOL", "RIC", "Instrument_Name", 
           "Country", "Currency", "Exchange", "ICB", "Free_Float", "Capfactor", "Shares", "Close_unadjusted_local", "FX_local_to_Index_Currency"]

# Developed Universe
Developed = pl.read_parquet(r"C:\Users\lbabbi\OneDrive - ISS\Desktop\Projects\SAMCO\V0_SAMCO\Universe\SWDACGV.parquet", columns=Columns).with_columns([
                            pl.col("Free_Float").cast(pl.Float64),
                            pl.col("Capfactor").cast(pl.Float64),
                            pl.col("Shares").cast(pl.Float64),
                            pl.col("Close_unadjusted_local").cast(pl.Float64),
                            pl.col("FX_local_to_Index_Currency").cast(pl.Float64),
                            pl.col("Date").cast(pl.Date)
                            ])

# Emerging Universe
Emerging = pl.read_parquet(r"C:\Users\lbabbi\OneDrive - ISS\Desktop\Projects\SAMCO\V0_SAMCO\Universe\SWEACGV.parquet", columns=Columns).with_columns([
                            pl.col("Free_Float").cast(pl.Float64),
                            pl.col("Capfactor").cast(pl.Float64),
                            pl.col("Shares").cast(pl.Float64),
                            pl.col("Close_unadjusted_local").cast(pl.Float64),
                            pl.col("FX_local_to_Index_Currency").cast(pl.Float64),
                            pl.col("Date").cast(pl.Date)
                            ])

# Entity_ID for matching same Companies
Entity_ID = pl.read_parquet(r"C:\Users\lbabbi\OneDrive - ISS\Desktop\Projects\SAMCO\V0_SAMCO\Entity_ID\Entity_ID.parquet").select(pl.col(["ENTITY_QID", "STOXX_ID",
                            "RELATIONSHIP_VALID_FROM", "RELATIONSHIP_VALID_TO"])).with_columns(
                                pl.col("RELATIONSHIP_VALID_FROM").cast(pl.Date()),
                                pl.col("RELATIONSHIP_VALID_TO").cast(pl.Date()))

# Add ENTITY_QID to main Frames
Developed = Developed.join(
                            Entity_ID,
                            left_on="Internal_Number",
                            right_on="STOXX_ID",
                            how="left"
                          ).unique(["Date", "Internal_Number"]).sort("Date", descending=False).with_columns(
                              pl.col("ENTITY_QID").fill_null(pl.col("Internal_Number"))).drop({"RELATIONSHIP_VALID_FROM", "RELATIONSHIP_VALID_TO"})

Emerging = Emerging.join(
                            Entity_ID,
                            left_on="Internal_Number",
                            right_on="STOXX_ID",
                            how="left"
                          ).unique(["Date", "Internal_Number"]).sort("Date", descending=False).with_columns(
                              pl.col("ENTITY_QID").fill_null(pl.col("Internal_Number"))).drop({"RELATIONSHIP_VALID_FROM", "RELATIONSHIP_VALID_TO"})

##################################
######Add Cutoff Information######
##################################
Columns = ["validDate", "stoxxId", "currency", "closePrice", "shares"]

# Read the Parquet and add the Review Date Column 
Securities_Cutoff = pl.read_parquet(r"C:\Users\lbabbi\OneDrive - ISS\Desktop\Projects\SAMCO\V0_SAMCO\Securities_Cutoff\Securities_Cutoff.parquet", columns=Columns).with_columns([
                      pl.col("closePrice").cast(pl.Float64),
                      pl.col("shares").cast(pl.Float64),
                      pl.col("validDate").cast(pl.Utf8).str.strptime(pl.Date, "%Y%m%d")
                      ]).join(pl.read_csv(r"C:\Users\lbabbi\OneDrive - ISS\Desktop\Projects\SAMCO\V0_SAMCO\Dates\Review_Date-QUARTERLY.csv").with_columns(
                        pl.col("Review").cast(pl.Utf8).str.strptime(pl.Date, "%m/%d/%Y"),
                        pl.col("Cutoff").cast(pl.Utf8).str.strptime(pl.Date, "%m/%d/%Y")
                      ), left_on="validDate", right_on="Cutoff", how="left")

FX_Cutoff = pl.read_parquet(r"C:\Users\lbabbi\OneDrive - ISS\Desktop\Projects\SAMCO\V0_SAMCO\Securities_Cutoff\FX_Historical.parquet").with_columns(
                            pl.col("Cutoff").cast(pl.Date)
)

# Add these information to the Developed and Emerging Universes
Developed = (
    Developed
    .join(
        Securities_Cutoff,
        left_on=["Date", "Internal_Number"],
        right_on=["Review", "stoxxId"],
        how="left"
    )
    .with_columns([
        # Fill null values in "currency" with the values from "Currency"
        pl.col("currency").fill_null(pl.col("Currency")),
    ])
    .drop("Currency")  # Drop the "Currency" column after filling nulls
    .rename({
        "validDate": "Cutoff",
        "closePrice": "Close_unadjusted_local_Cutoff",
        "shares": "Shares_Cutoff",
        "currency": "Currency"
    })
)

# Add FX_Cutoff
Developed = Developed.join(FX_Cutoff, on=["Cutoff", "Currency"], how="left")

Emerging = (
    Emerging
    .join(
        Securities_Cutoff,
        left_on=["Date", "Internal_Number"],
        right_on=["Review", "stoxxId"],
        how="left"
    )
    .with_columns([
        # Fill null values in "currency" with the values from "Currency"
        pl.col("currency").fill_null(pl.col("Currency")),
    ])
    .drop("Currency")  # Drop the "Currency" column after filling nulls
    .rename({
        "validDate": "Cutoff",
        "closePrice": "Close_unadjusted_local_Cutoff",
        "shares": "Shares_Cutoff",
        "currency": "Currency"
    })
)

# Add FX_Cutoff
Emerging = Emerging.join(FX_Cutoff, on=["Cutoff", "Currency"], how="left")

##################################
#########Drop Empty Rows##########
##################################
Developed = Developed.filter(~((pl.col("FX_local_to_Index_Currency_Cutoff").is_null()) | (pl.col("Close_unadjusted_local_Cutoff").is_null()) | (pl.col("Shares_Cutoff").is_null())))
Emerging = Emerging.filter(~((pl.col("FX_local_to_Index_Currency_Cutoff").is_null()) | (pl.col("Close_unadjusted_local_Cutoff").is_null()) | (pl.col("Shares_Cutoff").is_null())))

# Calculate Free/Full MCAP USD for Developed Universe
Developed = Developed.with_columns(
                                    (pl.col("Free_Float") * pl.col("Capfactor") * pl.col("Close_unadjusted_local_Cutoff") * pl.col("FX_local_to_Index_Currency_Cutoff") * pl.col("Shares_Cutoff"))
                                    .alias("Free_Float_MCAP_USD_Cutoff"),
                                    (pl.col("Close_unadjusted_local_Cutoff") * pl.col("FX_local_to_Index_Currency_Cutoff") * pl.col("Shares_Cutoff"))
                                    .alias("Full_MCAP_USD_Cutoff")
                                  )

# Calculate Free/Full MCAP USD for Emerging Universe
Emerging = Emerging.with_columns(
                                    (pl.col("Free_Float") * pl.col("Capfactor") * pl.col("Close_unadjusted_local_Cutoff") * pl.col("FX_local_to_Index_Currency_Cutoff") * pl.col("Shares_Cutoff"))
                                    .alias("Free_Float_MCAP_USD_Cutoff"),
                                    (pl.col("Close_unadjusted_local_Cutoff") * pl.col("FX_local_to_Index_Currency_Cutoff") * pl.col("Shares_Cutoff"))
                                    .alias("Full_MCAP_USD_Cutoff")
                                  )

# Check if there is any Free_Float_MCAP_USD_Cutoff Empty
Emerging = Emerging.filter(pl.col("Free_Float_MCAP_USD_Cutoff") > 0)
Developed = Developed.filter(pl.col("Free_Float_MCAP_USD_Cutoff") > 0)

###################################
#######Aggregate Companies#########
###################################

Developed_Aggregate = Developed.select(pl.col(["Date", "Internal_Number", "Instrument_Name", "ENTITY_QID", "Country", "Free_Float_MCAP_USD_Cutoff", "Full_MCAP_USD_Cutoff"])).group_by(
                                        ["Date", "ENTITY_QID"]).agg([
                                            pl.col("Country").first().alias("Country"),
                                            pl.col("Internal_Number").first().alias("Internal_Number"),
                                            pl.col("Instrument_Name").first().alias("Instrument_Name"),
                                            pl.col("Free_Float_MCAP_USD_Cutoff").sum().alias("Free_Float_MCAP_USD_Cutoff_Company"),
                                            pl.col("Full_MCAP_USD_Cutoff").sum().alias("Full_MCAP_USD_Cutoff_Company")
                                        ]).sort(["Date", "ENTITY_QID"])

Emerging_Aggregate = Emerging.select(pl.col(["Date", "Internal_Number", "Instrument_Name", "ENTITY_QID", "Country", "Free_Float_MCAP_USD_Cutoff", "Full_MCAP_USD_Cutoff"])).group_by(
                                        ["Date", "ENTITY_QID"]).agg([
                                            pl.col("Country").first().alias("Country"),
                                            pl.col("Internal_Number").first().alias("Internal_Number"),
                                            pl.col("Instrument_Name").first().alias("Instrument_Name"),
                                            pl.col("Free_Float_MCAP_USD_Cutoff").sum().alias("Free_Float_MCAP_USD_Cutoff_Company"),
                                            pl.col("Full_MCAP_USD_Cutoff").sum().alias("Full_MCAP_USD_Cutoff_Company")
                                        ]).sort(["Date", "ENTITY_QID"])

###################################
####Creation of main GMSR Frame####
###################################
GMSR_Frame = pl.DataFrame({
                            "Date": pl.Series(dtype=pl.Date),
                            "GMSR_Developed": pl.Series(dtype=pl.Float64),
                            "GMSR_Emerging": pl.Series(dtype=pl.Float64),
                            "GMSR_Emerging_Upper": pl.Series(dtype=pl.Float64),
                            "GMSR_Emerging_Lower": pl.Series(dtype=pl.Float64),
})

# Calculate GMSR for Developed/Emerging Universes
for date in Developed["Date"].unique():
    temp_Developed = Developed_Aggregate.filter(pl.col("Date") == date)

    temp_Developed = temp_Developed.sort(["Full_MCAP_USD_Cutoff_Company"], descending=True)
    temp_Developed = temp_Developed.with_columns(
                                                    (pl.col("Free_Float_MCAP_USD_Cutoff_Company") / pl.col("Free_Float_MCAP_USD_Cutoff_Company").sum()).alias("Weight_Cutoff")
    )

    temp_Developed = temp_Developed.with_columns(
                                                    (pl.col("Weight_Cutoff").cum_sum()).alias("CumWeight_Cutoff")
    )

    New_Data = pl.DataFrame({
                                "Date": [date],
                                "GMSR_Developed": [temp_Developed.filter(pl.col("CumWeight_Cutoff") >= Percentage).head(1)["Full_MCAP_USD_Cutoff_Company"].to_numpy()[0]],
                                "GMSR_Emerging": [temp_Developed.filter(pl.col("CumWeight_Cutoff") >= Percentage).head(1)["Full_MCAP_USD_Cutoff_Company"].to_numpy()[0] / 2],
                                "GMSR_Emerging_Upper": [temp_Developed.filter(pl.col("CumWeight_Cutoff") >= Percentage).head(1)["Full_MCAP_USD_Cutoff_Company"].to_numpy()[0] / 2 * Upper_Limit],
                                "GMSR_Emerging_Lower": [temp_Developed.filter(pl.col("CumWeight_Cutoff") >= Percentage).head(1)["Full_MCAP_USD_Cutoff_Company"].to_numpy()[0] / 2 * Lower_Limit],
    })

    GMSR_Frame = GMSR_Frame.vstack(New_Data)

###################################
#####Filtering from StartDate######
###################################
Emerging_Aggregate = Emerging_Aggregate.filter(pl.col("Date") >= Starting_Date)

#################################
##Start the Size Classification##
#################################
Output_Standard_Index = pl.DataFrame({
    "Date": pl.Series([], dtype=pl.Date),
    "Internal_Number": pl.Series([], dtype=pl.Utf8),
    "Instrument_Name": pl.Series([], dtype=pl.Utf8),
    "ENTITY_QID": pl.Series([], dtype=pl.Utf8),
    "Country": pl.Series([], dtype=pl.Utf8),
    "Free_Float_MCAP_USD_Cutoff_Company": pl.Series([], dtype=pl.Float64),
    "Full_MCAP_USD_Cutoff_Company": pl.Series([], dtype=pl.Float64),
    "Weight_Cutoff": pl.Series([], dtype=pl.Float64),
    "CumWeight_Cutoff": pl.Series([], dtype=pl.Float64),
    "Size": pl.Series([], dtype=pl.Utf8),
    "Case": pl.Series([], dtype=pl.Utf8),
    "Shadow_Company": pl.Series([], dtype=pl.Boolean)

})

Output_Count_Standard_Index = pl.DataFrame({
    "Country": pl.Series([], dtype=pl.Utf8),
    "Count": pl.Series([], dtype=pl.UInt32),
    "Date": pl.Series([], dtype=pl.Date),
})

with pd.ExcelWriter(Output_File, engine='xlsxwriter') as writer:
    for date in Emerging_Aggregate.select(["Date"]).unique().sort("Date").to_series():

        # Keep only a slice of Frame with the current Date
        temp_Emerging_Aggregate = Emerging_Aggregate.filter(pl.col("Date") == date)

        for country in temp_Emerging_Aggregate.select("Country").unique().sort("Country").to_series():
            # Retrieve the current Bounds
            Lower_GMSR = GMSR_Frame.select(["GMSR_Emerging_Lower", "Date"]).filter(pl.col("Date") == date).to_numpy()[0][0]
            Upper_GMSR = GMSR_Frame.select(["GMSR_Emerging_Upper", "Date"]).filter(pl.col("Date") == date).to_numpy()[0][0]
            
            # First Review Date where Standard Index is created
            if date == Starting_Date: 
                temp_Country = temp_Emerging_Aggregate.filter((pl.col("Date") == date) & (pl.col("Country") == country))

                # Sort in each Country the Companies by Full MCAP USD Cutoff
                temp_Country = temp_Country.sort("Full_MCAP_USD_Cutoff_Company", descending=True)

                # Calculate their CumWeight_Cutoff
                temp_Country = temp_Country.with_columns(
                                (pl.col("Free_Float_MCAP_USD_Cutoff_Company") / pl.col("Free_Float_MCAP_USD_Cutoff_Company").sum()).alias("Weight_Cutoff"),
                                (((pl.col("Free_Float_MCAP_USD_Cutoff_Company") / pl.col("Free_Float_MCAP_USD_Cutoff_Company").sum()).cum_sum())).alias("CumWeight_Cutoff")
                )

                # Check where the top 85% (crossing it) lands us on the Curve
                TopPercentage = temp_Country.select(["Date", "Internal_Number", "Instrument_Name", "ENTITY_QID", "Country", "Free_Float_MCAP_USD_Cutoff_Company",
                                "Full_MCAP_USD_Cutoff_Company", "Weight_Cutoff", "CumWeight_Cutoff"]).filter(
                                pl.col("CumWeight_Cutoff") < Percentage).vstack(temp_Country.select(["Date", "Internal_Number", "Instrument_Name", "ENTITY_QID", "Country", 
                                "Free_Float_MCAP_USD_Cutoff_Company", "Full_MCAP_USD_Cutoff_Company", "Weight_Cutoff", "CumWeight_Cutoff"]).filter(pl.col("CumWeight_Cutoff") >= Percentage).head(1))
                
                #################
                # Case Analysis #
                #################

                # Best case where we land inside the box # 
                if (TopPercentage.tail(1).select("Full_MCAP_USD_Cutoff_Company").to_numpy()[0][0] >= Lower_GMSR) & (TopPercentage.tail(1).select("Full_MCAP_USD_Cutoff_Company").to_numpy()[0][0] <= Upper_GMSR):

                    # Check how different is the CumWeight from Target Coverage
                    TopPercentage = TopPercentage.with_columns(
                                                (abs(pl.col("CumWeight_Cutoff") - Percentage)).alias("CumWeight_Cutoff_Difference")
                    )

                    # Check if CumWeight of the Company right across the Upper GMSR is > 90%
                    if TopPercentage.tail(1).select(pl.col("CumWeight_Cutoff")).to_numpy()[0][0] > Right_Limit:
                        next

                    # If CumWeight of the Company right across the Upper GMSR is <= 90%:
                    elif TopPercentage.tail(1).select(pl.col("CumWeight_Cutoff")).to_numpy()[0][0] <= Right_Limit:
                        # Filter by keeping only the closest CumWeight near to Percentage
                        TopPercentage = TopPercentage.head(TopPercentage["CumWeight_Cutoff_Difference"].arg_min() + 1)

                    TopPercentage = TopPercentage.with_columns(
                                                pl.lit("Standard").alias("Size")
                                        ).drop("CumWeight_Cutoff_Difference")
                    
                    TopPercentage = TopPercentage.with_columns(
                                                pl.lit("Inside").alias("Case")
                    )

                    # Check for Country_Cutoff
                    TopPercentage = Minimum_FreeFloat_Country(TopPercentage, Lower_GMSR, Upper_GMSR)

                    # Stack to Output_Standard_Index
                    Output_Standard_Index = Output_Standard_Index.vstack(TopPercentage)

                    # Save DataFrame to Excel
                    TopPercentage.to_pandas().to_excel(writer, sheet_name=f'{date}_{country}', index=False)

                    if Excel_Recap == True:
                        # Create and save the chart
                        chart_file = Curve_Plotting(TopPercentage, temp_Country, Lower_GMSR, Upper_GMSR)

                        # Insert the chart into the Excel file
                        workbook = writer.book
                        worksheet = writer.sheets[f'{date}_{country}']
                        worksheet.insert_image('H2', chart_file)

                # Case where we land below the box
                elif (TopPercentage.tail(1).select("Full_MCAP_USD_Cutoff_Company").to_numpy()[0][0] < Lower_GMSR):
                    # Keep only Companies whose Full_MCAP_USD_Cutoff_Company is at least equal or higher than Lowe GMSR
                    TopPercentage = TopPercentage.filter(pl.col("Full_MCAP_USD_Cutoff_Company") >= Lower_GMSR)

                    # In this case we do not care about the CumWeight_Cutoff
                    TopPercentage = TopPercentage.with_columns(
                                                pl.lit("Standard").alias("Size")
                                        )
                    
                    TopPercentage = TopPercentage.with_columns(
                                                pl.lit("Below").alias("Case")
                    )

                    # Check for Country_Cutoff
                    TopPercentage = Minimum_FreeFloat_Country(TopPercentage, Lower_GMSR, Upper_GMSR)

                    # Stack to Output_Standard_Index
                    Output_Standard_Index = Output_Standard_Index.vstack(TopPercentage)

                    # Save DataFrame to Excel
                    TopPercentage.to_pandas().to_excel(writer, sheet_name=f'{date}_{country}', index=False)

                    if Excel_Recap == True:
                        # Create and save the chart
                        chart_file = Curve_Plotting(TopPercentage, temp_Country, Lower_GMSR, Upper_GMSR)

                        # Insert the chart into the Excel file
                        workbook = writer.book
                        worksheet = writer.sheets[f'{date}_{country}']
                        worksheet.insert_image('H2', chart_file)

                # Case where we land above the box
                elif (TopPercentage.tail(1).select("Full_MCAP_USD_Cutoff_Company").to_numpy()[0][0] > Upper_GMSR):

                    # Check if there are still Companies in between the Upper and Lower GMSR
                    if len(temp_Country.filter((pl.col("Full_MCAP_USD_Cutoff_Company") <= Upper_GMSR) & (pl.col("Full_MCAP_USD_Cutoff_Company") >= Lower_GMSR))) > 0:

                        TopPercentage_Extension = temp_Country.filter(pl.col("Full_MCAP_USD_Cutoff_Company") >= Upper_GMSR).sort("Full_MCAP_USD_Cutoff_Company",
                            descending=True).filter(~pl.col("Internal_Number").is_in(TopPercentage.select(pl.col("Internal_Number")))).select(
                                ["Date", "Internal_Number", "Instrument_Name", "ENTITY_QID", "Country", "Free_Float_MCAP_USD_Cutoff_Company", "Full_MCAP_USD_Cutoff_Company", 
                                "Weight_Cutoff", "CumWeight_Cutoff"]).vstack(temp_Country.filter(pl.col("Full_MCAP_USD_Cutoff_Company") < Upper_GMSR).sort("Full_MCAP_USD_Cutoff_Company",
                            descending=True).filter(~pl.col("Internal_Number").is_in(TopPercentage.select(pl.col("Internal_Number")))).select(
                                ["Date", "Internal_Number", "Instrument_Name", "ENTITY_QID", "Country", "Free_Float_MCAP_USD_Cutoff_Company",
                                "Full_MCAP_USD_Cutoff_Company", "Weight_Cutoff", "CumWeight_Cutoff"]).head(1)
                                )
                        
                        TopPercentage = TopPercentage.with_columns(
                                                pl.lit("Standard").alias("Size")
                                        )
                        
                        TopPercentage_Extension = TopPercentage_Extension.with_columns(
                                                pl.lit("Standard").alias("Size")
                                        )
                        
                        # Merge the initial Frame with the additions
                        TopPercentage = TopPercentage.vstack(TopPercentage_Extension)

                        TopPercentage = TopPercentage.with_columns(
                                                pl.lit("Above - Companies in between Upper and Lower GMSR").alias("Case")
                                )
                        
                        # Check for Country_Cutoff
                        TopPercentage = Minimum_FreeFloat_Country(TopPercentage, Lower_GMSR, Upper_GMSR)
                        
                        # Stack to Output_Standard_Index
                        Output_Standard_Index = Output_Standard_Index.vstack(TopPercentage)

                        # Save DataFrame to Excel
                        TopPercentage.to_pandas().to_excel(writer, sheet_name=f'{date}_{country}', index=False)

                        if Excel_Recap == True:
                            # Create and save the chart
                            chart_file = Curve_Plotting(TopPercentage, temp_Country, Lower_GMSR, Upper_GMSR)

                            # Insert the chart into the Excel file
                            workbook = writer.book
                            worksheet = writer.sheets[f'{date}_{country}']
                            worksheet.insert_image('H2', chart_file)

                    # Case where we do not have any company in between the Upper and Lower GMSR
                    elif len(temp_Country.filter((pl.col("Full_MCAP_USD_Cutoff_Company") <= Upper_GMSR) & (pl.col("Full_MCAP_USD_Cutoff_Company") >= Lower_GMSR))) == 0:
                        # Try to get as close as possible to Upper GMSR
                        TopPercentage_Extension = temp_Country.filter(pl.col("Full_MCAP_USD_Cutoff_Company") >= Lower_GMSR).sort("Full_MCAP_USD_Cutoff_Company", descending=True,
                                                    ).filter(~pl.col("Internal_Number").is_in(TopPercentage.select(pl.col("Internal_Number")))).select(
                                                    ["Date", "Internal_Number", "Instrument_Name", "ENTITY_QID", "Country", "Free_Float_MCAP_USD_Cutoff_Company", 
                                                    "Full_MCAP_USD_Cutoff_Company", "Weight_Cutoff", "CumWeight_Cutoff"])
                        
                        TopPercentage = TopPercentage.with_columns(
                                                pl.lit("Standard").alias("Size")
                                        )
                        
                        TopPercentage_Extension = TopPercentage_Extension.with_columns(
                                                pl.lit("Standard").alias("Size")
                                        )
                        
                        # Merge the initial Frame with the additions
                        TopPercentage = TopPercentage.vstack(TopPercentage_Extension)

                        
                        TopPercentage = TopPercentage.with_columns(
                                                pl.lit("Above - No Companies in between Upper and Lower GMSR").alias("Case")
                                )
                        
                        # Check for Country_Cutoff
                        TopPercentage = Minimum_FreeFloat_Country(TopPercentage, Lower_GMSR, Upper_GMSR)
                        
                        # Stack to Output_Standard_Index
                        Output_Standard_Index = Output_Standard_Index.vstack(TopPercentage)

                        # Save DataFrame to Excel
                        TopPercentage.to_pandas().to_excel(writer, sheet_name=f'{date}_{country}', index=False)

                        if Excel_Recap == True:

                            # Create and save the chart
                            chart_file = Curve_Plotting(TopPercentage, temp_Country, Lower_GMSR, Upper_GMSR)

                            # Insert the chart into the Excel file
                            workbook = writer.book
                            worksheet = writer.sheets[f'{date}_{country}']
                            worksheet.insert_image('H2', chart_file)

                # Create the Output_Count_Standard_Index for future rebalacing
                Output_Count_Standard_Index = Output_Count_Standard_Index.vstack(TopPercentage.group_by("Country").agg(
                    pl.len().alias("Count"),
                    pl.col("Date").first().alias("Date")
                ).sort("Count", descending=True))

            # 